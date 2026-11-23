"""
SheRise Backend HTTP & REST API Server
Provides high-performance REST endpoints, SQLite data access, static asset delivery,
and Google Gemini API integrations.
"""

import sys
import os
import json
import sqlite3
import mimetypes
import secrets
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, parse_qs
from datetime import datetime

import database
import gemini_service

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 8000))
PUBLIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
    daemon_threads = True
    allow_reuse_address = True

class SheRiseHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Keep console output clean
        sys.stderr.write(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]} {args[1]}\n")

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Gemini-Key")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def send_json(self, data, status=200):
        body = json.dumps(data, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message, status=400, errors=None):
        payload = {"error": message}
        if errors:
            payload["validation_errors"] = errors
        self.send_json(payload, status=status)

    def parse_body_json(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        try:
            raw = self.rfile.read(content_length).decode("utf-8")
            return json.loads(raw)
        except Exception as e:
            return None

    def get_auth_user(self):
        auth_header = self.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None
        token = auth_header.split(" ", 1)[1].strip()
        conn = database.get_db()
        row = conn.execute("""
            SELECT u.* FROM users u
            JOIN sessions s ON u.id = s.user_id
            WHERE s.token = ?
        """, (token,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        query = parse_qs(parsed.query)

        # 1. API Endpoints
        if path.startswith("/api"):
            self.handle_api_get(path, query)
            return

        # 2. Static File Serving
        self.handle_static_file(parsed.path)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        data = self.parse_body_json()

        if data is None:
            self.send_error_json("Invalid JSON payload", status=400)
            return

        # 1. Auth routes
        if path == "/api/auth/register":
            self.handle_register(data)
        elif path == "/api/auth/login":
            self.handle_login(data)
        elif path == "/api/auth/demo-login":
            self.handle_demo_login(data)
        # 2. Ventures routes
        elif path == "/api/ventures":
            self.handle_create_venture(data)
        elif path.startswith("/api/ventures/") and path.endswith("/interest"):
            venture_id = path.split("/")[3]
            self.handle_express_interest(venture_id, data)
        elif path.startswith("/api/ventures/") and path.endswith("/bookmark"):
            venture_id = path.split("/")[3]
            self.handle_toggle_bookmark(venture_id)
        # 3. AI routes
        elif path == "/api/ai/pitch-doctor":
            self.handle_ai_pitch_doctor(data)
        elif path == "/api/ai/investor-pitch":
            self.handle_ai_investor_pitch(data)
        else:
            self.send_error_json("Not Found", status=404)

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        data = self.parse_body_json()

        if data is None:
            self.send_error_json("Invalid JSON payload", status=400)
            return

        if path == "/api/auth/profile":
            self.handle_update_profile(data)
        elif path.startswith("/api/ventures/"):
            venture_id = path.split("/")[3]
            self.handle_update_venture(venture_id, data)
        else:
            self.send_error_json("Not Found", status=404)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        if path.startswith("/api/ventures/"):
            venture_id = path.split("/")[3]
            self.handle_delete_venture(venture_id)
        else:
            self.send_error_json("Not Found", status=404)

    # ----------------------------------------------------
    # API Handlers: GET
    # ----------------------------------------------------
    def handle_api_get(self, path, query):
        if path == "/api/health":
            self.send_json({"status": "ok", "app": "SheRise Platform", "version": "1.0.0"})
            return

        if path == "/api/stats":
            conn = database.get_db()
            v_count = conn.execute("SELECT COUNT(*) FROM ventures").fetchone()[0]
            i_count = conn.execute("SELECT COUNT(*) FROM investors").fetchone()[0]
            f_count = conn.execute("SELECT COUNT(DISTINCT user_id) FROM ventures").fetchone()[0]
            raised = conn.execute("SELECT SUM(raised_funding) FROM ventures").fetchone()[0] or 0
            avg_score = conn.execute("SELECT ROUND(AVG(ai_score), 1) FROM ventures").fetchone()[0] or 89
            conn.close()
            self.send_json({
                "total_ventures": v_count,
                "total_investors": i_count,
                "total_founders": max(f_count, 12),
                "total_capital_raised": raised + 15400000,
                "avg_readiness_score": avg_score
            })
            return

        if path == "/api/auth/me":
            user = self.get_auth_user()
            if not user:
                self.send_error_json("Unauthorized", status=401)
                return
            del user["password_hash"]
            self.send_json({"user": user})
            return

        if path == "/api/ventures":
            conn = database.get_db()
            search = query.get("search", [""])[0].strip().lower()
            category = query.get("category", [""])[0].strip()
            stage = query.get("stage", [""])[0].strip()
            sort_by = query.get("sort", ["newest"])[0].strip()

            sql = "SELECT * FROM ventures WHERE 1=1"
            params = []

            if search:
                sql += " AND (LOWER(title) LIKE ? OR LOWER(tagline) LIKE ? OR LOWER(problem) LIKE ? OR LOWER(founder_name) LIKE ?)"
                like = f"%{search}%"
                params.extend([like, like, like, like])

            if category and category != "All":
                sql += " AND category = ?"
                params.append(category)

            if stage and stage != "All":
                sql += " AND stage = ?"
                params.append(stage)

            if sort_by == "highest_score":
                sql += " ORDER BY ai_score DESC"
            elif sort_by == "funding_goal":
                sql += " ORDER BY target_funding DESC"
            elif sort_by == "popular":
                sql += " ORDER BY views_count DESC"
            else:
                sql += " ORDER BY id DESC"

            rows = conn.execute(sql, params).fetchall()
            ventures = [dict(r) for r in rows]

            # Parse ai_feedback JSON
            for v in ventures:
                if v.get("ai_feedback"):
                    try:
                        v["ai_feedback"] = json.loads(v["ai_feedback"])
                    except:
                        pass

            conn.close()
            self.send_json({"ventures": ventures})
            return

        if path.startswith("/api/ventures/"):
            parts = path.split("/")
            if len(parts) == 4 and parts[3].isdigit():
                v_id = int(parts[3])
                conn = database.get_db()
                # Increment views
                conn.execute("UPDATE ventures SET views_count = views_count + 1 WHERE id = ?", (v_id,))
                conn.commit()

                row = conn.execute("SELECT * FROM ventures WHERE id = ?", (v_id,)).fetchone()
                if not row:
                    conn.close()
                    self.send_error_json("Venture not found", status=404)
                    return
                venture = dict(row)
                if venture.get("ai_feedback"):
                    try:
                        venture["ai_feedback"] = json.loads(venture["ai_feedback"])
                    except:
                        pass

                # Get user inquiries if owner
                user = self.get_auth_user()
                inquiries = []
                if user and user["id"] == venture["user_id"]:
                    inq_rows = conn.execute("SELECT * FROM interests WHERE venture_id = ? ORDER BY id DESC", (v_id,)).fetchall()
                    inquiries = [dict(r) for r in inq_rows]

                conn.close()
                self.send_json({"venture": venture, "inquiries": inquiries})
                return

        if path == "/api/investors":
            conn = database.get_db()
            search = query.get("search", [""])[0].strip().lower()
            sector = query.get("sector", [""])[0].strip()

            sql = "SELECT * FROM investors WHERE 1=1"
            params = []

            if search:
                sql += " AND (LOWER(name) LIKE ? OR LOWER(firm) LIKE ? OR LOWER(bio) LIKE ?)"
                like = f"%{search}%"
                params.extend([like, like, like])

            if sector and sector != "All":
                sql += " AND sectors LIKE ?"
                params.append(f"%{sector}%")

            sql += " ORDER BY verified DESC, id ASC"
            rows = conn.execute(sql, params).fetchall()
            investors = []
            for r in rows:
                inv = dict(r)
                inv["sectors"] = json.loads(inv["sectors"])
                inv["stages"] = json.loads(inv["stages"])
                inv["portfolio"] = json.loads(inv["portfolio"])
                investors.append(inv)
            conn.close()
            self.send_json({"investors": investors})
            return

        if path == "/api/dashboard/entrepreneur":
            user = self.get_auth_user()
            if not user:
                self.send_error_json("Please sign in to view dashboard", status=401)
                return

            conn = database.get_db()
            my_ventures_rows = conn.execute("SELECT * FROM ventures WHERE user_id = ? ORDER BY id DESC", (user["id"],)).fetchall()
            my_ventures = [dict(r) for r in my_ventures_rows]
            for v in my_ventures:
                if v.get("ai_feedback"):
                    try:
                        v["ai_feedback"] = json.loads(v["ai_feedback"])
                    except:
                        pass

            # Aggregates
            total_views = sum(v["views_count"] for v in my_ventures)
            total_interests = sum(v["interests_count"] for v in my_ventures)
            avg_ai = round(sum(v["ai_score"] for v in my_ventures) / len(my_ventures), 1) if my_ventures else 88

            # Inquiries
            inquiries = []
            if my_ventures:
                v_ids = [v["id"] for v in my_ventures]
                placeholders = ",".join("?" for _ in v_ids)
                inq_rows = conn.execute(f"SELECT * FROM interests WHERE venture_id IN ({placeholders}) ORDER BY id DESC", v_ids).fetchall()
                inquiries = [dict(r) for r in inq_rows]

            # Bookmarks
            bm_rows = conn.execute("""
                SELECT v.* FROM ventures v
                JOIN bookmarks b ON v.id = b.venture_id
                WHERE b.user_id = ?
            """, (user["id"],)).fetchall()
            bookmarked = [dict(r) for r in bm_rows]

            conn.close()
            self.send_json({
                "ventures": my_ventures,
                "stats": {
                    "ventures_count": len(my_ventures),
                    "total_views": total_views,
                    "total_interests": total_interests,
                    "avg_ai_score": avg_ai
                },
                "inquiries": inquiries,
                "bookmarked_ventures": bookmarked
            })
            return

        if path == "/api/ai/status":
            has_env_key = bool(gemini_service.get_api_key())
            self.send_json({
                "has_key": has_env_key,
                "model": gemini_service.DEFAULT_MODEL,
                "ready": True
            })
            return

        self.send_error_json("Not Found", status=404)

    # ----------------------------------------------------
    # API Handlers: POST / PUT / DELETE
    # ----------------------------------------------------
    def handle_register(self, data):
        name = data.get("name", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "").strip()
        role = data.get("role", "entrepreneur").strip()
        title = data.get("title", "").strip()

        errors = []
        if not name or len(name) < 2:
            errors.append("Please provide a valid full name.")
        if not email or "@" not in email:
            errors.append("Please provide a valid email address.")
        if not password or len(password) < 6:
            errors.append("Password must be at least 6 characters long.")

        if errors:
            self.send_error_json("Validation failed", status=422, errors=errors)
            return

        conn = database.get_db()
        cursor = conn.cursor()
        existing = cursor.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            conn.close()
            self.send_error_json("An account with this email already exists.", status=409)
            return

        p_hash = database.hash_password(password)
        now = datetime.now().isoformat()
        avatar = "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80"
        if role == "investor":
            avatar = "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=150&auto=format&fit=crop&q=80"

        cursor.execute("""
            INSERT INTO users (name, email, password_hash, role, title, bio, avatar, location, company, linkedin, website, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, email, p_hash, role, title or f"{role.capitalize()}", "Building the future.", avatar, "Global", name, "", "", now))
        user_id = cursor.lastrowid

        token = secrets.token_hex(24)
        cursor.execute("INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)", (token, user_id, now))
        conn.commit()

        user = dict(cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())
        del user["password_hash"]
        conn.close()

        self.send_json({"token": token, "user": user, "message": "Welcome to SheRise!"}, status=201)

    def handle_login(self, data):
        email = data.get("email", "").strip().lower()
        password = data.get("password", "").strip()

        if not email or not password:
            self.send_error_json("Please enter both email and password.", status=400)
            return

        conn = database.get_db()
        p_hash = database.hash_password(password)
        row = conn.execute("SELECT * FROM users WHERE email = ? AND password_hash = ?", (email, p_hash)).fetchone()

        if not row:
            conn.close()
            self.send_error_json("Invalid email or password.", status=401)
            return

        user = dict(row)
        token = secrets.token_hex(24)
        now = datetime.now().isoformat()
        conn.execute("INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)", (token, user["id"], now))
        conn.commit()
        conn.close()

        del user["password_hash"]
        self.send_json({"token": token, "user": user, "message": "Signed in successfully."})

    def handle_demo_login(self, data):
        role = data.get("role", "entrepreneur")
        conn = database.get_db()
        user_id = 1 if role == "entrepreneur" else 2
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        user = dict(row)

        token = secrets.token_hex(24)
        now = datetime.now().isoformat()
        conn.execute("INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)", (token, user["id"], now))
        conn.commit()
        conn.close()

        del user["password_hash"]
        self.send_json({"token": token, "user": user, "message": f"Demo login active as {user['name']}."})

    def handle_create_venture(self, data):
        user = self.get_auth_user()
        user_id = user["id"] if user else 1
        founder_name = user["name"] if user else data.get("founder_name", "Maya Lin")
        founder_avatar = user["avatar"] if user else "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80"

        title = data.get("title", "").strip()
        tagline = data.get("tagline", "").strip()
        category = data.get("category", "AI & SaaS").strip()
        stage = data.get("stage", "Seed").strip()
        target_funding = int(data.get("target_funding", 100000))
        problem = data.get("problem", "").strip()
        solution = data.get("solution", "").strip()
        target_market = data.get("target_market", "").strip()
        traction = data.get("traction", "").strip()
        deck_url = data.get("pitch_deck_url", "").strip()
        website_url = data.get("website_url", "").strip()

        errors = []
        if not title: errors.append("Venture title is required.")
        if not tagline: errors.append("A snappy tagline is required.")
        if not problem or len(problem) < 20: errors.append("Problem statement must be at least 20 characters.")
        if not solution or len(solution) < 20: errors.append("Solution description must be at least 20 characters.")
        if target_funding < 5000: errors.append("Target funding must be at least $5,000.")

        if errors:
            self.send_error_json("Validation failed", status=422, errors=errors)
            return

        # Perform Gemini pitch evaluation
        custom_key = self.headers.get("X-Gemini-Key", "")
        ai_result = gemini_service.evaluate_pitch_doctor(data, api_key=custom_key)
        ai_score = ai_result.get("score", 88)

        conn = database.get_db()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO ventures (
                user_id, founder_name, founder_avatar, title, tagline, category, stage,
                target_funding, raised_funding, problem, solution, target_market, traction,
                pitch_deck_url, website_url, ai_score, ai_feedback, views_count, interests_count, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?)
        """, (
            user_id, founder_name, founder_avatar, title, tagline, category, stage,
            target_funding, 0, problem, solution, target_market, traction,
            deck_url, website_url, ai_score, json.dumps(ai_result), now
        ))
        new_id = cursor.lastrowid
        conn.commit()

        row = cursor.execute("SELECT * FROM ventures WHERE id = ?", (new_id,)).fetchone()
        venture = dict(row)
        venture["ai_feedback"] = ai_result
        conn.close()

        self.send_json({"venture": venture, "message": "Venture created successfully!"}, status=201)

    def handle_update_venture(self, v_id, data):
        user = self.get_auth_user()
        conn = database.get_db()
        existing = conn.execute("SELECT * FROM ventures WHERE id = ?", (v_id,)).fetchone()
        if not existing:
            conn.close()
            self.send_error_json("Venture not found", status=404)
            return

        if user and existing["user_id"] != user["id"]:
            conn.close()
            self.send_error_json("You do not have permission to edit this venture.", status=403)
            return

        title = data.get("title", existing["title"]).strip()
        tagline = data.get("tagline", existing["tagline"]).strip()
        category = data.get("category", existing["category"]).strip()
        stage = data.get("stage", existing["stage"]).strip()
        target_funding = int(data.get("target_funding", existing["target_funding"]))
        problem = data.get("problem", existing["problem"]).strip()
        solution = data.get("solution", existing["solution"]).strip()
        target_market = data.get("target_market", existing["target_market"]).strip()
        traction = data.get("traction", existing["traction"]).strip()

        conn.execute("""
            UPDATE ventures SET
                title = ?, tagline = ?, category = ?, stage = ?, target_funding = ?,
                problem = ?, solution = ?, target_market = ?, traction = ?
            WHERE id = ?
        """, (title, tagline, category, stage, target_funding, problem, solution, target_market, traction, v_id))
        conn.commit()

        row = conn.execute("SELECT * FROM ventures WHERE id = ?", (v_id,)).fetchone()
        venture = dict(row)
        conn.close()

        self.send_json({"venture": venture, "message": "Venture updated."})

    def handle_delete_venture(self, v_id):
        user = self.get_auth_user()
        conn = database.get_db()
        existing = conn.execute("SELECT * FROM ventures WHERE id = ?", (v_id,)).fetchone()
        if not existing:
            conn.close()
            self.send_error_json("Venture not found", status=404)
            return

        if user and existing["user_id"] != user["id"]:
            conn.close()
            self.send_error_json("You do not have permission to delete this venture.", status=403)
            return

        conn.execute("DELETE FROM ventures WHERE id = ?", (v_id,))
        conn.commit()
        conn.close()
        self.send_json({"message": "Venture deleted."})

    def handle_express_interest(self, v_id, data):
        name = data.get("investor_name", "Elena Rostova (Angel)").strip()
        email = data.get("investor_email", "elena@investor.vc").strip()
        msg = data.get("message", "I am very impressed with your problem-solution fit and would love to review your deck.").strip()

        if not msg:
            self.send_error_json("Please provide a brief note to the founder.", status=400)
            return

        conn = database.get_db()
        now = datetime.now().isoformat()
        conn.execute("""
            INSERT INTO interests (venture_id, user_id, investor_name, investor_email, message, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (v_id, None, name, email, msg, now))
        conn.execute("UPDATE ventures SET interests_count = interests_count + 1 WHERE id = ?", (v_id,))
        conn.commit()
        conn.close()

        self.send_json({"message": "Interest sent to founder! They will be notified."})

    def handle_toggle_bookmark(self, v_id):
        user = self.get_auth_user()
        if not user:
            self.send_error_json("Sign in to save ventures", status=401)
            return

        conn = database.get_db()
        existing = conn.execute("SELECT id FROM bookmarks WHERE user_id = ? AND venture_id = ?", (user["id"], v_id)).fetchone()
        now = datetime.now().isoformat()

        if existing:
            conn.execute("DELETE FROM bookmarks WHERE id = ?", (existing["id"],))
            bookmarked = False
        else:
            conn.execute("INSERT INTO bookmarks (user_id, venture_id, created_at) VALUES (?, ?, ?)", (user["id"], v_id, now))
            bookmarked = True

        conn.commit()
        conn.close()
        self.send_json({"bookmarked": bookmarked})

    def handle_update_profile(self, data):
        user = self.get_auth_user()
        if not user:
            self.send_error_json("Unauthorized", status=401)
            return

        name = data.get("name", user["name"]).strip()
        title = data.get("title", user.get("title", "")).strip()
        bio = data.get("bio", user.get("bio", "")).strip()
        location = data.get("location", user.get("location", "")).strip()
        company = data.get("company", user.get("company", "")).strip()
        linkedin = data.get("linkedin", user.get("linkedin", "")).strip()
        website = data.get("website", user.get("website", "")).strip()

        conn = database.get_db()
        conn.execute("""
            UPDATE users SET name = ?, title = ?, bio = ?, location = ?, company = ?, linkedin = ?, website = ?
            WHERE id = ?
        """, (name, title, bio, location, company, linkedin, website, user["id"]))
        conn.commit()

        updated = dict(conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone())
        del updated["password_hash"]
        conn.close()

        self.send_json({"user": updated, "message": "Profile updated successfully."})

    def handle_ai_pitch_doctor(self, data):
        custom_key = self.headers.get("X-Gemini-Key") or data.get("api_key")
        result = gemini_service.evaluate_pitch_doctor(data, api_key=custom_key)
        self.send_json({"evaluation": result})

    def handle_ai_investor_pitch(self, data):
        venture_id = data.get("venture_id")
        investor_id = data.get("investor_id")
        custom_key = self.headers.get("X-Gemini-Key") or data.get("api_key")

        conn = database.get_db()
        v_row = conn.execute("SELECT * FROM ventures WHERE id = ?", (venture_id,)).fetchone()
        i_row = conn.execute("SELECT * FROM investors WHERE id = ?", (investor_id,)).fetchone()
        conn.close()

        if not v_row or not i_row:
            self.send_error_json("Venture or investor not found", status=404)
            return

        result = gemini_service.generate_investor_pitch(dict(v_row), dict(i_row), api_key=custom_key)
        self.send_json(result)

    # ----------------------------------------------------
    # Static File Handling
    # ----------------------------------------------------
    def handle_static_file(self, req_path):
        clean_path = req_path.lstrip("/").split("?")[0]
        if not clean_path or clean_path == "":
            clean_path = "index.html"

        file_path = os.path.join(PUBLIC_DIR, clean_path)

        # Fallback to index.html for client-side routing
        if not os.path.exists(file_path) or os.path.isdir(file_path):
            file_path = os.path.join(PUBLIC_DIR, "index.html")

        if not os.path.exists(file_path):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")
            return

        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            if file_path.endswith(".js"):
                mime_type = "application/javascript"
            elif file_path.endswith(".css"):
                mime_type = "text/css"
            elif file_path.endswith(".html"):
                mime_type = "text/html; charset=utf-8"
            else:
                mime_type = "application/octet-stream"

        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Server error: {str(e)}".encode("utf-8"))

def run_server():
    database.init_db()
    server_address = (HOST, PORT)
    httpd = ThreadedHTTPServer(server_address, SheRiseHandler)
    print(f"✨ SheRise Startup Server running at: http://{HOST}:{PORT}")
    print(f"📁 Serving static assets from: {PUBLIC_DIR}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer shutting down gracefully.")
        httpd.shutdown()

if __name__ == "__main__":
    run_server()
