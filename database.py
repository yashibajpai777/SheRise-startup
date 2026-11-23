"""
SheRise Database Module
Manages SQLite schema, operations, and seed data for female founders & investors.
"""

import sqlite3
import os
import json
import hashlib
import secrets
from datetime import datetime

DB_PATH = os.environ.get("SHERISE_DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "sherise.db"))

def get_db():
    # Ensure directory exists if custom path provided
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    salt = os.environ.get("SHERISE_SALT", "sherise_secure_salt_2026")
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'entrepreneur', -- 'entrepreneur' or 'investor'
        title TEXT,
        bio TEXT,
        avatar TEXT,
        location TEXT,
        company TEXT,
        linkedin TEXT,
        website TEXT,
        created_at TEXT NOT NULL
    )
    """)

    # Ventures / Business Ideas table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ventures (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        founder_name TEXT NOT NULL,
        founder_avatar TEXT,
        title TEXT NOT NULL,
        tagline TEXT NOT NULL,
        category TEXT NOT NULL,
        stage TEXT NOT NULL,
        target_funding INTEGER NOT NULL DEFAULT 100000,
        raised_funding INTEGER NOT NULL DEFAULT 0,
        problem TEXT NOT NULL,
        solution TEXT NOT NULL,
        target_market TEXT NOT NULL,
        traction TEXT,
        pitch_deck_url TEXT,
        website_url TEXT,
        ai_score INTEGER DEFAULT 88,
        ai_feedback TEXT,
        views_count INTEGER DEFAULT 0,
        interests_count INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # Investors directory table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS investors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        firm TEXT NOT NULL,
        role TEXT NOT NULL,
        avatar TEXT,
        bio TEXT NOT NULL,
        sectors TEXT NOT NULL, -- JSON array
        stages TEXT NOT NULL,  -- JSON array
        check_size_min INTEGER NOT NULL,
        check_size_max INTEGER NOT NULL,
        location TEXT NOT NULL,
        verified INTEGER DEFAULT 1,
        portfolio TEXT NOT NULL, -- JSON array
        thesis TEXT NOT NULL
    )
    """)

    # Inquiries / Expressed Interest table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venture_id INTEGER NOT NULL,
        user_id INTEGER,
        investor_name TEXT NOT NULL,
        investor_email TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (venture_id) REFERENCES ventures(id) ON DELETE CASCADE
    )
    """)

    # Bookmarks table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookmarks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        venture_id INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(user_id, venture_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (venture_id) REFERENCES ventures(id) ON DELETE CASCADE
    )
    """)

    # Auth Sessions / Tokens table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    conn.commit()

    # Seed data if empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        seed_data(cursor, conn)

    conn.close()

def seed_data(cursor, conn):
    now = datetime.now().isoformat()

    # 1. Seed Users (1 Founder, 1 Investor demo)
    users_data = [
        (
            1,
            "Maya Lin",
            "maya@bionova.health",
            hash_password("password123"),
            "entrepreneur",
            "Founder & CEO at BioNova Health",
            "Biomedical researcher turned founder. Passionate about women's preventative oncology and accessible diagnostic diagnostics.",
            "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80",
            "San Francisco, CA",
            "BioNova Health",
            "https://linkedin.com/in/mayalin-demo",
            "https://bionova.health",
            now
        ),
        (
            2,
            "Elena Rostova",
            "elena@purplehorizon.vc",
            hash_password("password123"),
            "investor",
            "General Partner at Purple Horizon Ventures",
            "Early-stage investor backing underrepresented founders in HealthTech, AI, and Sustainable Supply Chains. Backed 30+ female-led startups.",
            "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=150&auto=format&fit=crop&q=80",
            "New York, NY",
            "Purple Horizon Ventures",
            "https://linkedin.com/in/elenarostova-demo",
            "https://purplehorizon.vc",
            now
        ),
        (
            3,
            "Amina Diop",
            "amina@solarharvest.tech",
            hash_password("password123"),
            "entrepreneur",
            "Co-Founder & CTO at SolarHarvest",
            "CleanTech engineer passionate about distributed renewable micro-grids for decentralized agriculture and food storage.",
            "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80",
            "Austin, TX",
            "SolarHarvest Tech",
            "https://linkedin.com/in/aminadiop-demo",
            "https://solarharvest.tech",
            now
        )
    ]

    cursor.executemany("""
    INSERT INTO users (id, name, email, password_hash, role, title, bio, avatar, location, company, linkedin, website, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, users_data)

    # 2. Seed Ventures
    ventures_data = [
        (
            1,
            1,
            "Maya Lin",
            "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80",
            "BioNova Health",
            "AI-powered microfluidic home testing for hormone biomarkers and early cancer detection.",
            "HealthTech",
            "Seed",
            750000,
            520000,
            "Women face an average 4-year delay in hormonal health and oncology diagnosis due to invasive, expensive, and infrequent lab visits.",
            "BioNova creates a thumb-sized cartridge that pairs with any smartphone to read salivary and blood biomarkers in 7 minutes with lab-grade precision.",
            "$42B global women's health diagnostic market, starting with PCOS and perimenopause management in North America.",
            "3,200 waitlist subscribers, completed 2 IRB-approved clinical pilot validations, and $18k MRR in pre-orders.",
            "https://example.com/bionova-deck.pdf",
            "https://bionova.health",
            94,
            json.dumps({
                "score": 94,
                "readiness_level": "High Investor Readiness",
                "executive_pitch": "BioNova Health provides lab-grade, 7-minute hormonal diagnostic home tests powered by patented microfluidics and smartphone AI, capturing a $42B underserved women's health market.",
                "strengths": [
                    "Strong clinical validation with completed IRB pilot studies",
                    "Exceptional problem-solution fit with recurring consumer revenue model",
                    "Proprietary microfluidic patent portfolio"
                ],
                "growth_areas": [
                    "Clarify FDA 510(k) regulatory clearance timeline and reimbursement pathway",
                    "Establish B2B enterprise partnerships with corporate wellness benefits"
                ]
            }),
            1420,
            18,
            now
        ),
        (
            2,
            3,
            "Amina Diop",
            "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80",
            "SolarHarvest Tech",
            "Modular solar cold-chain storage lockers empowering women agricultural co-ops.",
            "CleanTech & Climate",
            "Early Traction",
            500000,
            280000,
            "Over 35% of harvested fresh produce spoils before reaching regional markets because smallholder farmers cannot afford grid-tied cold rooms.",
            "SolarHarvest installs pay-as-you-store modular refrigerated hubs powered by IoT smart battery solar arrays, extending crop shelf-life from 2 to 21 days.",
            "$14B cold-chain logistics market across emerging agricultural corridors.",
            "4 hubs deployed, 620 farmer co-op members active, reducing post-harvest loss by 78% while generating $12k monthly network revenue.",
            "https://example.com/solarharvest-deck.pdf",
            "https://solarharvest.tech",
            91,
            json.dumps({
                "score": 91,
                "readiness_level": "High Investor Readiness",
                "executive_pitch": "SolarHarvest Tech delivers off-grid, modular solar refrigeration to agricultural co-ops, eliminating 78% of crop spoilage through a predictable pay-per-crate subscription.",
                "strengths": [
                    "Tangible unit economics with demonstrated 78% spoilage reduction",
                    "High social impact combined with profitable B2B recurring cash flow",
                    "Strong grassroots founder distribution network"
                ],
                "growth_areas": [
                    "Define hardware manufacturing supply chain and warranty reserve models",
                    "Explore carbon credit offset monetization opportunities"
                ]
            }),
            980,
            12,
            now
        ),
        (
            3,
            1,
            "Camille Laurent",
            "https://images.unsplash.com/photo-1567532939604-b6b5b0db2604?w=150&auto=format&fit=crop&q=80",
            "Aura Finance",
            "Algorithmic wealth builder and micro-angel syndicate platform tailored for women.",
            "FinTech",
            "Early Traction",
            1200000,
            650000,
            "Women face a $1.2M lifetime wealth accumulation gap and are 40% less likely to participate in private markets or angel syndicates.",
            "Aura combines automated goal-based index investing with zero-minimum accredited angel pooling for female-founded startups.",
            "Over 65 million working women in the US and Europe seeking holistic wealth planning and equity investments.",
            "$4.2M in Assets Under Management (AUM) within 6 months, 2,800 active monthly depositors, 4.9 App Store rating.",
            "https://example.com/aurafinance-deck.pdf",
            "https://aurafinance.io",
            89,
            json.dumps({
                "score": 89,
                "readiness_level": "Strong Investment Potential",
                "executive_pitch": "Aura Finance bridges the gender wealth gap with an intuitive wealth platform combining algorithmic index savings and syndicate angel investments.",
                "strengths": [
                    "Rapid AUM growth and extremely high user engagement (4.9 rating)",
                    "Strong viral community referral loops lowering CAC"
                ],
                "growth_areas": [
                    "Highlight licensing and compliance regulatory safeguards (SEC/FINRA partner bank structure)",
                    "Show clear lifetime value (LTV) to customer acquisition cost (CAC) cohort curves"
                ]
            }),
            2150,
            24,
            now
        ),
        (
            4,
            1,
            "Priya Sharma",
            "https://images.unsplash.com/photo-1573497019940-1c28c88b4f3e?w=150&auto=format&fit=crop&q=80",
            "Kura AI",
            "Autonomous multi-agent customer operations copilot for female-led Shopify brands.",
            "AI & SaaS",
            "Prototype / MVP",
            400000,
            150000,
            "Independent boutique e-commerce founders spend up to 25 hours per week responding to repetitive customer inquiries, shipping updates, and return tickets.",
            "Kura AI deploys brand-calibrated autonomous agents that resolve 82% of omnichannel support tickets instantly with empathy and brand tone.",
            "$9.5B e-commerce customer support software space with 2.8M Shopify stores.",
            "28 paying pilot stores, 45,000 queries handled, 94% customer satisfaction rating, 82% automated resolution rate.",
            "https://example.com/kura-deck.pdf",
            "https://kura.ai",
            87,
            json.dumps({
                "score": 87,
                "readiness_level": "Promising Seed Stage",
                "executive_pitch": "Kura AI is an autonomous support workforce for modern e-commerce brands, automating 82% of support tickets with genuine brand voice.",
                "strengths": [
                    "High customer satisfaction and proven operational hours saved",
                    "Zero-friction Shopify App store installation pipeline"
                ],
                "growth_areas": [
                    "Demonstrate defensibility against general LLM wrappers through proprietary integrations",
                    "Add automated cross-sell and revenue attribution metrics"
                ]
            }),
            840,
            9,
            now
        ),
        (
            5,
            3,
            "Dr. Sophia Vance",
            "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150&auto=format&fit=crop&q=80",
            "TerraBloom Bio",
            "Mycelium-based regenerative packaging replacing petroleum polystyrene.",
            "CleanTech & Climate",
            "Seed",
            900000,
            420000,
            "Expanded polystyrene takes 500+ years to degrade and fills 30% of global landfills, yet protective packaging demand is surging.",
            "TerraBloom grows 100% home-compostable protective custom packaging molded in 5 days using agricultural hemp byproduct and fungal mycelium.",
            "$32B sustainable protective packaging market driven by EU and US carbon packaging bans.",
            "Contract signed with 2 national luxury cosmetics brands for 120,000 packaging units in 2026.",
            "https://example.com/terrabloom-deck.pdf",
            "https://terrabloom.bio",
            93,
            json.dumps({
                "score": 93,
                "readiness_level": "High Investor Readiness",
                "executive_pitch": "TerraBloom Bio produces high-performance mycelium packaging that replaces styrofoam at cost parity while composting in your garden in 45 days.",
                "strengths": [
                    "Secured commercial supplier purchase orders with luxury brands",
                    "Cost parity with synthetic foam at automated pilot scale",
                    "Patented spore growth inhibition technology"
                ],
                "growth_areas": [
                    "Detail scaling of bio-foundry production facilities and CAPEX requirements",
                    "Detail drop-test certification standards across electronics vs consumer goods"
                ]
            }),
            1790,
            15,
            now
        ),
        (
            6,
            1,
            "Zainab Al-Mansoor",
            "https://images.unsplash.com/photo-1573496799652-408c2ac9fe98?w=150&auto=format&fit=crop&q=80",
            "Mentora Kids",
            "Neurodivergent learning companion adapting real-time cognitive curricula for neurodiverse girls.",
            "EdTech",
            "Idea",
            250000,
            60000,
            "Girls with ADHD and autism are diagnosed on average 5 years later than boys and lack personalized learning tools adapted to masking behaviors.",
            "Mentora Kids uses game-based cognitive pacing and speech-emotional recognition to tailor STEM and literacy lessons in real time.",
            "$8.5B special education and neurodiversity assistive technology sector.",
            "Surveyed 450 pediatric psychologists and 1,200 parents; prototype tested with 40 neurodiverse students showing a 3x increase in task completion.",
            "https://example.com/mentora-deck.pdf",
            "https://mentorakids.org",
            85,
            json.dumps({
                "score": 85,
                "readiness_level": "High Early Stage Potential",
                "executive_pitch": "Mentora Kids provides adaptive AI learning adventures designed specifically for the unique diagnostic and learning profiles of neurodivergent girls.",
                "strengths": [
                    "Addresses an underserved, deeply emotionally resonant market",
                    "Strong backing from pediatric educators and psychologist advisory board"
                ],
                "growth_areas": [
                    "Build out complete interactive MVP prototype",
                    "Secure school district pilot agreements alongside direct-to-parent subscription"
                ]
            }),
            630,
            7,
            now
        )
    ]

    cursor.executemany("""
    INSERT INTO ventures (id, user_id, founder_name, founder_avatar, title, tagline, category, stage, target_funding, raised_funding, problem, solution, target_market, traction, pitch_deck_url, website_url, ai_score, ai_feedback, views_count, interests_count, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, ventures_data)

    # 3. Seed Investors
    investors_data = [
        (
            1,
            "Elena Rostova",
            "Purple Horizon Ventures",
            "General Partner",
            "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=150&auto=format&fit=crop&q=80",
            "Investing in audacious female founders reimagining healthcare, climate resilience, and foundational infrastructure.",
            json.dumps(["HealthTech", "CleanTech & Climate", "AI & SaaS"]),
            json.dumps(["Pre-seed", "Seed"]),
            50000,
            500000,
            "New York, NY",
            1,
            json.dumps(["CureBio", "VerdeGrid", "FeminaCare", "AuraScale"]),
            "We back technical and clinical female founders building high-moat products in sectors with massive tailwinds. We write $100k-$500k initial checks and lead rounds."
        ),
        (
            2,
            "Sarah Jenkins, MD",
            "Femovate Angel Syndicate",
            "Syndicate Lead & Angel Investor",
            "https://images.unsplash.com/photo-1573497019236-17f8177b81e8?w=150&auto=format&fit=crop&q=80",
            "Physician-investor dedicated to female-focused healthtech, diagnostic devices, and biotech solutions.",
            json.dumps(["HealthTech", "BioTech"]),
            json.dumps(["Seed", "Series A"]),
            25000,
            250000,
            "Boston, MA",
            1,
            json.dumps(["EndoScan", "MamaCare", "VitalGlow"]),
            "We invest in scientifically validated innovations solving real diagnostic, reproductive, and longevity gaps for women globally."
        ),
        (
            3,
            "Tara Reynolds",
            "Valkyrie Capital",
            "Managing Director",
            "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80",
            "Seed stage venture capital firm investing exclusively in female and non-binary tech leaders across AI, SaaS, and FinTech.",
            json.dumps(["FinTech", "AI & SaaS", "E-commerce"]),
            json.dumps(["Pre-seed", "Seed", "Series A"]),
            100000,
            1500000,
            "San Francisco, CA",
            1,
            json.dumps(["PayPulse", "KnitCommerce", "LexiAI", "OmniRoute"]),
            "We look for founders with deep domain obsession, rapid customer execution velocity, and clear software network effects."
        ),
        (
            4,
            "Ananya Sen",
            "GreenLotus Impact Fund",
            "Partner",
            "https://images.unsplash.com/photo-1567532939604-b6b5b0db2604?w=150&auto=format&fit=crop&q=80",
            "Decarbonization, circular economy, and regenerative food systems champion backing female climate innovators.",
            json.dumps(["CleanTech & Climate", "BioTech"]),
            json.dumps(["Idea", "Early Traction", "Seed"]),
            50000,
            750000,
            "London & Singapore",
            1,
            json.dumps(["AlgaeFiber", "SoilCarbon IQ", "RePack Global"]),
            "Capital combined with supply-chain off-taker networks to help female climate entrepreneurs cross the commercialization chasm."
        ),
        (
            5,
            "Jessica Morales",
            "Catalyst Women Angels",
            "Founding Angel",
            "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150&auto=format&fit=crop&q=80",
            "Former 2x exited founder now actively writing 15-20 angel checks per year in consumer, community, and EdTech.",
            json.dumps(["EdTech", "E-commerce", "Creative & Media"]),
            json.dumps(["Idea", "Prototype / MVP", "Seed"]),
            10000,
            100000,
            "Austin, TX",
            1,
            json.dumps(["BloomBox", "SkillSprout", "DuoCraft"]),
            "Hands-on mentorship from zero to one million ARR. I love bold consumer propositions with strong organic community retention."
        )
    ]

    cursor.executemany("""
    INSERT INTO investors (id, name, firm, role, avatar, bio, sectors, stages, check_size_min, check_size_max, location, verified, portfolio, thesis)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, investors_data)

    conn.commit()

# Initialize DB on load
init_db()
