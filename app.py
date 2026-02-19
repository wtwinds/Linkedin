from flask import Flask, render_template, request, session, redirect
from pymongo import MongoClient
import random
from flask_mail import Mail, Message
from flask import flash
import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# MongoDB
client = MongoClient(config.MONGO_URI)
db = client["wtwinds"]
users = db["users"]
posts=db["posts"]

# Mail
app.config.update(
    MAIL_SERVER=config.MAIL_SERVER,
    MAIL_PORT=config.MAIL_PORT,
    MAIL_USE_TLS=config.MAIL_USE_TLS,
    MAIL_USERNAME=config.MAIL_USERNAME,
    MAIL_PASSWORD=config.MAIL_PASSWORD
)
mail = Mail(app)


# ================= LOGIN =================
@app.route("/", methods=["GET", "POST"])
def login():

    # 🔥 AUTO LOGIN (DB based)
    if session.get("email"):
        user = users.find_one({"email": session["email"]})
        if user:
            if user.get("profile_completed"):
                return redirect("/dashboard")
            else:
                return redirect("/signup")

    if "step" not in session:
        session["step"] = "email"

    if request.method == "POST":
        action = request.form.get("action")

        # ================= SEND OTP =================
        if action == "send_otp":
            email = request.form.get("email")
            otp = str(random.randint(100000, 999999))

            session["otp"] = otp
            session["email"] = email
            session["step"] = "otp"

            try:
                msg = Message(
                    "WT Winds OTP",
                    sender=config.MAIL_USERNAME,
                    recipients=[email]
                )
                msg.body = f"Your WT Winds OTP is: {otp}"
                mail.send(msg)
                flash("OTP sent to your email", "success")
            except Exception as e:
                print("MAIL ERROR:", e)
                flash("Mail error - Check SMTP", "danger")

        # ================= RESEND OTP =================
        elif action == "resend_otp":
            email = session.get("email")
            if not email:
                return redirect("/")

            otp = str(random.randint(100000, 999999))
            session["otp"] = otp

            try:
                msg = Message(
                    "WT Winds OTP",
                    sender=config.MAIL_USERNAME,
                    recipients=[email]
                )
                msg.body = f"Your new OTP is: {otp}"
                mail.send(msg)
                flash("New OTP sent successfully", "info")
            except Exception as e:
                print("RESEND ERROR:", e)
                flash("Failed to resend OTP", "danger")

        # ================= VERIFY OTP =================
        elif action == "verify_otp":
            entered = request.form.get("otp")

            if entered == session.get("otp"):
                email = session["email"]

                # 🔥 CHECK EXISTING USER
                user = users.find_one({"email": email})

                if not user:
                    users.insert_one({
                        "email": email,
                        "verified": True,
                        "profile_completed": False
                    })

                session["verified"] = True
                return redirect("/signup")

            else:
                flash("Invalid OTP ❌", "danger")

    return render_template("login.html", step=session.get("step"))

# ================= CHANGE EMAIL =================
@app.route("/change-email")
def change_email():
    session.clear()
    return redirect("/")

# ================= PROFILE PAGE =================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if not session.get("email"):
        return redirect("/")

    if request.method == "POST":
        name = request.form.get("name")
        age = request.form.get("age")
        college = request.form.get("college")
        profession = request.form.get("profession")

        users.update_one(
            {"email": session["email"]},
            {"$set": {
                "name": name,
                "age": age,
                "college": college,
                "profession": profession,
                "profile_completed": True
            }}
        )

        return redirect("/dashboard")

    return render_template("profile.html")


# ================= DASHBOARD =================
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if not session.get("email"):
        return redirect("/")

    # CREATE POST
    if request.method == "POST":
        content = request.form.get("content")
        if content:
            posts.insert_one({
                "email": session["email"],
                "content": content,
                "like": [],
                "comments": []
            })

    user = users.find_one({"email": session["email"]})
    # Profile not completed → redirect
    if not user or not user.get("profile_completed"):
        return redirect("/signup")

    all_posts = list(posts.find().sort("_id", -1))

    return render_template("dashboard.html", user=user, posts=all_posts)

# ================= LIKE POST =================
@app.route("/like/<post_id>")
def like_post(post_id):
    if not session.get("email"):
        return redirect("/")

    from bson import ObjectId

    post = posts.find_one({"_id": ObjectId(post_id)})
    user_email = session["email"]

    if user_email in post.get("likes", []):
        # Unlike
        posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$pull": {"likes": user_email}}
        )
    else:
        # Like
        posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$push": {"likes": user_email}}
        )

    return redirect("/dashboard")

# ================= COMMENT =================
@app.route("/comment/<post_id>", methods=["POST"])
def comment_post(post_id):
    if not session.get("email"):
        return redirect("/")

    from bson import ObjectId

    text = request.form.get("comment")
    if text:
        posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$push": {
                "comments": {
                    "user": session["email"],
                    "text": text
                }
            }}
        )

    return redirect("/dashboard")

#==================Delete Post============
@app.route("/delete-post/<post_id>")
def delete_post(post_id):
    if not session.get("email"):
        return redirect("/")

    from bson import ObjectId

    posts.delete_one({
        "_id": ObjectId(post_id),
        "email": session["email"]  # Only delete own post
    })

    return redirect("/dashboard")

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
