"""
BuildSync REST API Backend
Framework: Python Flask with modular structure and mock/persistent DB handlers.
Endpoints: /api/auth, /api/projects, /api/escrow, /api/logs, /api/admin
"""

import os
import time
import hashlib
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

# In-Memory State Sync for high-performance demo / fallback when MySQL isn't directly connected
IN_MEMORY_DB = {
    "users": [
        {
            "id": 1,
            "full_name": "Vikram Sharma",
            "email": "vikram@example.com",
            "phone": "+91 98765 43210",
            "role": "client",
            "avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150"
        },
        {
            "id": 2,
            "full_name": "Ramesh Carpentry & Interiors",
            "email": "ramesh.wood@example.com",
            "phone": "+91 91234 56789",
            "role": "contractor",
            "trade": "Carpentry",
            "rating": 4.9,
            "kyc_status": "verified",
            "aadhaar_pan": "XXXX-XXXX-8812 / ABXPK****K",
            "avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150"
        },
        {
            "id": 3,
            "full_name": "BuildSync Master Admin",
            "email": "admin@buildsync.com",
            "phone": "+91 90000 00000",
            "role": "admin",
            "avatar": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150"
        }
    ],
    "projects": [
        {
            "id": 101,
            "title": "Luxury Modular Kitchen & Custom Wardrobes",
            "client_id": 1,
            "client_name": "Vikram Sharma",
            "contractor_id": 2,
            "contractor_name": "Ramesh Carpentry & Interiors",
            "project_type": "Custom Wardrobe & Modular Kitchen",
            "property_address": "Flat 402, Seawood Towers, Bandra West, Mumbai",
            "square_footage": 850,
            "estimated_total_cost": 485000.00,
            "escrow_deposited": 485000.00,
            "status": "in_progress",
            "price_locked": True,
            "created_at": "2026-09-15 10:30:00"
        }
    ],
    "milestones": [
        {
            "id": 1,
            "project_id": 101,
            "phase_number": 1,
            "title": "Phase 1: Site Measurement & 3D Design Approval",
            "description": "Laser scanning, CAD drawing sign-off, and raw plywood procurement.",
            "amount": 120000.00,
            "status": "released",
            "approved_at": "2026-09-18 14:20:00"
        },
        {
            "id": 2,
            "project_id": 101,
            "phase_number": 2,
            "title": "Phase 2: Carcass Fabrication & Laminate Pressing",
            "description": "Assembly of Marine Plywood frames and Blum soft-close fittings.",
            "amount": 215000.00,
            "status": "in_review",
            "approved_at": None
        },
        {
            "id": 3,
            "project_id": 101,
            "phase_number": 3,
            "title": "Phase 3: On-Site Installation & Lighting Integration",
            "description": "Mounting shutters, LED strip channels, and final inspection.",
            "amount": 150000.00,
            "status": "locked",
            "approved_at": None
        }
    ],
    "daily_logs": [
        {
            "id": 501,
            "project_id": 101,
            "contractor_id": 2,
            "log_date": "2026-10-01",
            "summary_text": "Completed carcass box alignment for master bedroom wardrobe. Installed 12 pairs of Blum soft-close hinges. Plywood edges edge-banded with 2mm PVC.",
            "voice_note_url": "https://actions.google.com/sounds/v1/speech/voice_sample.ogg",
            "photo_1": "https://images.unsplash.com/photo-1503387762-592deb58ef4e?w=600",
            "photo_2": "https://images.unsplash.com/photo-1618221195710-dd6b41faaea6?w=600",
            "photo_3": "https://images.unsplash.com/photo-1581094794329-c8112a89af12?w=600",
            "attendance_count": 5
        }
    ],
    "transactions": [
        {
            "id": 9001,
            "project_id": 101,
            "milestone_id": 1,
            "payer_name": "Vikram Sharma",
            "payee_name": "Ramesh Carpentry",
            "amount": 120000.00,
            "platform_fee": 6000.00,
            "net_payout": 114000.00,
            "transaction_type": "milestone_release",
            "reference_hash": "0x8f2a7b1c3d9e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a",
            "timestamp": "2026-09-18 14:20:12"
        }
    ],
    "materials": [
        {"id": 1, "name": "BWP Marine Plywood (18mm)", "category": "Carpentry", "wholesale_price": 115.00, "retail_price": 145.00, "unit": "sq.ft", "guarantee_price": 115.00},
        {"id": 2, "name": "Teak Veneer (4mm Grade A)", "category": "Interiors", "wholesale_price": 180.00, "retail_price": 230.00, "unit": "sq.ft", "guarantee_price": 180.00},
        {"id": 3, "name": "UltraTech Super Cement", "category": "Masonry", "wholesale_price": 370.00, "retail_price": 420.00, "unit": "bag (50kg)", "guarantee_price": 370.00},
        {"id": 4, "name": "TMT Steel Bars (12mm FE500D)", "category": "Structural", "wholesale_price": 62.00, "retail_price": 74.00, "unit": "kg", "guarantee_price": 62.00},
        {"id": 5, "name": "Soft-Close Hydraulic Hinges", "category": "Hardware", "wholesale_price": 450.00, "retail_price": 580.00, "unit": "pair", "guarantee_price": 450.00},
        {"id": 6, "name": "Asian Paints Royal Emulsion", "category": "Finishing", "wholesale_price": 420.00, "retail_price": 510.00, "unit": "liter", "guarantee_price": 420.00}
    ]
}

# ----------------- ROUTE BLUEPRINTS & HANDLERS -----------------

@app.route("/")
def serve_index():
    return app.send_static_file("index.html")

# 1. AUTH & RBAC ENDPOINTS
@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    data = request.json or {}
    email_or_phone = data.get("identifier", "").strip()
    role = data.get("role", "client").lower()
    
    # Simple auth lookup
    user = next((u for u in IN_MEMORY_DB["users"] if u["role"] == role), None)
    if not user:
        user = IN_MEMORY_DB["users"][0]
        
    return jsonify({
        "status": "success",
        "message": f"Successfully authenticated as {role.capitalize()}",
        "user": user,
        "token": f"token_{int(time.time())}_{user['id']}"
    })

@app.route("/api/auth/register", methods=["POST"])
def auth_register():
    data = request.json or {}
    role = data.get("role", "client")
    name = data.get("full_name", "New User")
    email = data.get("email", f"user_{int(time.time())}@buildsync.com")
    
    new_user = {
        "id": len(IN_MEMORY_DB["users"]) + 1,
        "full_name": name,
        "email": email,
        "phone": data.get("phone", "+91 99999 88888"),
        "role": role,
        "trade": data.get("trade", "Carpentry"),
        "avatar": "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150"
    }
    IN_MEMORY_DB["users"].append(new_user)
    
    return jsonify({
        "status": "success",
        "message": "Account created successfully!",
        "user": new_user,
        "token": f"token_{int(time.time())}_{new_user['id']}"
    })

# 2. PROJECTS & INSTANT COST ESTIMATOR ENDPOINTS
@app.route("/api/projects/estimate", methods=["POST"])
def calculate_estimate():
    data = request.json or {}
    project_type = data.get("project_type", "Custom Wardrobe")
    sqft = float(data.get("square_footage", 200))
    material_grade = data.get("material_grade", "Premium BWP Plywood")
    
    # Pricing Matrix Logic
    base_rates = {
        "Custom Wardrobe": {"labor": 350, "material": 650},
        "Full Home Renovation": {"labor": 450, "material": 950},
        "Structural Masonry": {"labor": 250, "material": 450},
        "Interior Painting & Polish": {"labor": 120, "material": 180}
    }
    
    selected_rate = base_rates.get(project_type, {"labor": 300, "material": 600})
    labor_cost = sqft * selected_rate["labor"]
    material_cost = sqft * selected_rate["material"]
    
    if material_grade == "Luxury Hardwood & Veneer":
        material_cost *= 1.35
    elif material_grade == "Standard Commercial":
        material_cost *= 0.85
        
    subtotal = labor_cost + material_cost
    gst_18 = subtotal * 0.18
    total_cost = subtotal + gst_18
    
    return jsonify({
        "status": "success",
        "breakdown": {
            "project_type": project_type,
            "square_footage": sqft,
            "material_grade": material_grade,
            "labor_cost": round(labor_cost, 2),
            "material_cost": round(material_cost, 2),
            "subtotal": round(subtotal, 2),
            "tax_gst": round(gst_18, 2),
            "total_estimated_cost": round(total_cost, 2),
            "recommended_milestones": [
                {"phase": 1, "name": "3D Design & Raw Material Lock", "percentage": 25, "amount": round(total_cost * 0.25, 2)},
                {"phase": 2, "name": "Fabrication & Structural Work", "percentage": 45, "amount": round(total_cost * 0.45, 2)},
                {"phase": 3, "name": "Final Installation & Polish", "percentage": 30, "amount": round(total_cost * 0.30, 2)}
            ]
        }
    })

@app.route("/api/projects", methods=["GET"])
def get_projects():
    return jsonify({"status": "success", "projects": IN_MEMORY_DB["projects"]})

# 3. ESCROW & MILESTONE PAYMENTS ENDPOINTS
@app.route("/api/escrow/approve", methods=["POST"])
def approve_milestone():
    data = request.json or {}
    milestone_id = int(data.get("milestone_id", 0))
    
    milestone = next((m for m in IN_MEMORY_DB["milestones"] if m["id"] == milestone_id), None)
    if not milestone:
        return jsonify({"status": "error", "message": "Milestone not found"}), 404
        
    if milestone["status"] == "released":
        return jsonify({"status": "warning", "message": "Milestone payout has already been released!"}), 400
        
    # Update state
    milestone["status"] = "released"
    milestone["approved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    amount = milestone["amount"]
    platform_fee = amount * 0.05
    net_payout = amount - platform_fee
    
    ref_hash = "0x" + hashlib.sha256(f"release_{milestone_id}_{time.time()}".encode()).hexdigest()
    
    tx = {
        "id": len(IN_MEMORY_DB["transactions"]) + 9001,
        "project_id": milestone["project_id"],
        "milestone_id": milestone["id"],
        "payer_name": "Vikram Sharma",
        "payee_name": "Ramesh Carpentry",
        "amount": amount,
        "platform_fee": platform_fee,
        "net_payout": net_payout,
        "transaction_type": "milestone_release",
        "reference_hash": ref_hash,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    IN_MEMORY_DB["transactions"].append(tx)
    
    # Unlock next milestone if present
    next_m = next((m for m in IN_MEMORY_DB["milestones"] if m["phase_number"] == milestone["phase_number"] + 1), None)
    if next_m and next_m["status"] == "locked":
        next_m["status"] = "funded"
        
    return jsonify({
        "status": "success",
        "message": f"Milestone #{milestone['phase_number']} approved! ₹{net_payout:,.2f} released to contractor.",
        "milestone": milestone,
        "transaction": tx
    })

# 4. FIELD WORKER DAILY LOGS ENDPOINTS
@app.route("/api/logs/upload", methods=["POST"])
def upload_daily_log():
    data = request.json or {}
    summary = data.get("summary", "Daily work completed on schedule.")
    photos = data.get("photos", [
        "https://images.unsplash.com/photo-1541888946425-d0fbb186a5b7?w=600",
        "https://images.unsplash.com/photo-1503387762-592deb58ef4e?w=600",
        "https://images.unsplash.com/photo-1618221195710-dd6b41faaea6?w=600"
    ])
    attendance = int(data.get("attendance", 4))
    
    new_log = {
        "id": len(IN_MEMORY_DB["daily_logs"]) + 501,
        "project_id": 101,
        "contractor_id": 2,
        "log_date": datetime.now().strftime("%Y-%m-%d"),
        "summary_text": summary,
        "voice_note_url": "https://actions.google.com/sounds/v1/speech/voice_sample.ogg",
        "photo_1": photos[0] if len(photos) > 0 else photos[0],
        "photo_2": photos[1] if len(photos) > 1 else photos[0],
        "photo_3": photos[2] if len(photos) > 2 else photos[0],
        "attendance_count": attendance
    }
    IN_MEMORY_DB["daily_logs"].insert(0, new_log)
    
    return jsonify({
        "status": "success",
        "message": "Daily field progress log synced & timeline feed updated!",
        "log": new_log
    })

@app.route("/api/logs", methods=["GET"])
def get_daily_logs():
    return jsonify({"status": "success", "logs": IN_MEMORY_DB["daily_logs"]})

@app.route("/api/materials", methods=["GET"])
def get_materials():
    return jsonify({"status": "success", "materials": IN_MEMORY_DB["materials"]})

# 5. ADMIN & SYSTEM METRICS ENDPOINTS
@app.route("/api/admin/overview", methods=["GET"])
def admin_overview():
    return jsonify({
        "status": "success",
        "metrics": {
            "active_projects": len(IN_MEMORY_DB["projects"]),
            "escrow_locked_val": 365000.00,
            "dispute_rate": "0.00%",
            "verified_contractors": 48,
            "total_payouts_processed": 1285000.00
        },
        "transactions": IN_MEMORY_DB["transactions"],
        "contractors_kyc": [
            {
                "name": "Ramesh Carpentry & Interiors",
                "trade": "Carpentry",
                "aadhaar_pan": "XXXX-XXXX-8812 / ABXPK****K",
                "status": "Verified",
                "projects_completed": 14,
                "rating": 4.9
            },
            {
                "name": "Apex Civil Masons & Co.",
                "trade": "Masonry",
                "aadhaar_pan": "XXXX-XXXX-1049 / BCNPM****L",
                "status": "Verified",
                "projects_completed": 9,
                "rating": 4.8
            },
            {
                "name": "Modern Space Decorators",
                "trade": "Interiors",
                "aadhaar_pan": "XXXX-XXXX-9902 / CKLPM****M",
                "status": "Pending Review",
                "projects_completed": 2,
                "rating": 4.6
            }
        ]
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 BuildSync REST API Server running at http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
