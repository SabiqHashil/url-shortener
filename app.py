import os
from datetime import datetime, timedelta
import pytz
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort
from models import db, Link
from utils import normalize_url, random_code


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///data.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    app.config["PREFERRED_URL_SCHEME"] = os.environ.get("URL_SCHEME", "http")

    # Initialize database
    db.init_app(app)
    with app.app_context():
        db.create_all()

    # Template filter for local time
    @app.template_filter("localtime")
    def localtime_filter(value):
        """Convert UTC datetime to local timezone and format as DD-MM-YYYY HH:MM"""
        if value is None:
            return ""
        local_tz = pytz.timezone("Asia/Kolkata")
        return value.astimezone(local_tz).strftime('%d-%m-%Y %H:%M')
    
    # Routes
    @app.get("/")
    def home():
        recent = Link.query.order_by(Link.created_at.desc()).limit(10).all()
        return render_template("index.html", recent=recent)

    @app.post("/shorten")
    def shorten():
        long_url = request.form.get("long_url", "")
        custom = request.form.get("custom_code", "").strip() or None
        expiry = request.form.get("expiry_hours", "").strip()
        try:
            long_url = normalize_url(long_url)
        except ValueError:
            flash("Please enter a valid URL.", "error")
            return redirect(url_for("home"))

        # Handle custom short code
        if custom:
            if len(custom) > 16 or not custom.isalnum():
                flash("Custom code must be alphanumeric and ≤ 16 chars.", "error")
                return redirect(url_for("home"))
            if Link.query.filter_by(code=custom).first():
                flash("That custom code is already taken.", "error")
                return redirect(url_for("home"))
            code = custom
        else:
            # generate a unique code
            code = random_code()
            while Link.query.filter_by(code=code).first():
                code = random_code()
        
        # Handle expiry time
        expires_at = None
        if expiry:
            try:
                hours = int(expiry)
                if hours > 0:
                    expires_at = datetime.utcnow() + timedelta(hours=hours)
            except ValueError:
                pass

        # Create new link
        link = Link(code=code, original_url=long_url, expires_at=expires_at)
        db.session.add(link)
        db.session.commit()
        short_url = url_for("resolve", code=code, _external=True)
        flash(f"Short URL created: {short_url}", "success")
        return redirect(url_for("home"))

    @app.get("/stats/<code>")
    def stats(code):
        link = Link.query.filter_by(code=code).first_or_404()
        return render_template("stats.html", link=link)

    # API endpoints
    @app.get("/api/shorten")
    def api_shorten_get():
        return jsonify({"message": "POST a JSON body to /api/shorten with url, optional code, expiry_hours"})

    @app.post("/api/shorten")
    def api_shorten():
        data = request.get_json(force=True, silent=True) or {}
        try:
            long_url = normalize_url(data.get("url", ""))
        except Exception:
            return jsonify({"error": "Invalid URL"}), 400

        code = data.get("code")
        if code:
            if len(code) > 16 or not str(code).isalnum():
                return jsonify({"error": "Invalid custom code"}), 400
            if Link.query.filter_by(code=code).first():
                return jsonify({"error": "Code already exists"}), 409
        else:
            code = random_code()
            while Link.query.filter_by(code=code).first():
                code = random_code()

        expires_at = None
        hours = data.get("expiry_hours")
        if isinstance(hours, (int, float)) and hours > 0:
            expires_at = datetime.utcnow() + timedelta(hours=int(hours))

        link = Link(code=code, original_url=long_url, expires_at=expires_at)
        db.session.add(link)
        db.session.commit()
        return jsonify({
            "code": code,
            "short_url": url_for("resolve", code=code, _external=True),
            "expires_at": link.expires_at.isoformat() if link.expires_at else None
        }), 201

    # Redirect short link
    @app.get("/<code>")
    def resolve(code):
        link = Link.query.filter_by(code=code).first()
        if not link:
            abort(404)
        if link.is_expired():
            flash("This short link has expired.", "error")
            return redirect(url_for("home"))
        link.clicks += 1
        db.session.commit()
        return redirect(link.original_url, code=302)

    # Error handler
    @app.errorhandler(404)
    def not_found(e):
        return render_template("base.html", content="<h2>404 Not Found</h2><p>That short code doesn't exist.</p>"), 404

    return app

# Create and run app
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
