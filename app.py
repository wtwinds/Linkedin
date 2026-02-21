from flask import Flask, render_template, request, session, redirect, flash
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import config
from bson import ObjectId

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# MongoDB
client = MongoClient(config.MONGO_URI)
db = client["wtwinds"]
users = db["users"]
posts = db["posts"]

# ================= HOME LOGIN =================
@app.route("/", methods=["GET", "POST"])
def login():

    # AUTO LOGIN
    if session.get("email"):
        user = users.find_one({"email": session["email"]})
        if user:
            if user.get("profile_completed"):
                return redirect("/dashboard")
            else:
                return redirect("/profile")

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = users.find_one({"email": email})

        if user and check_password_hash(user["password"], password):
            session["email"] = email
            flash("Login successful ✅", "success")

            if user.get("profile_completed"):
                return redirect("/dashboard")
            else:
                return redirect("/profile")
        else:
            flash("Invalid email or password ❌", "danger")

    return render_template("login.html")


# ================= SIGNUP =================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if users.find_one({"email": email}):
            flash("User already exists ⚠️", "warning")
            return redirect("/")

        users.insert_one({
            "email": email,
            "password": generate_password_hash(password),
            "profile_completed": False
        })

        session["email"] = email
        flash("Account created 🎉", "success")
        return redirect("/profile")

    return render_template("signup.html")


# ================= PROFILE =================
@app.route("/profile", methods=["GET", "POST"])
def profile():
    if not session.get("email"):
        return redirect("/")

    if request.method == "POST":
        users.update_one(
            {"email": session["email"]},
            {"$set": {
                "name": request.form.get("name"),
                "age": request.form.get("age"),
                "college": request.form.get("college"),
                "profession": request.form.get("profession"),
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

    if request.method == "POST":
        content = request.form.get("content")
        if content:
            posts.insert_one({
                "email": session["email"],
                "content": content,
                "likes": [],
                "comments": []
            })

    user = users.find_one({"email": session["email"]})
    if not user.get("profile_completed"):
        return redirect("/profile")

    all_posts = list(posts.find().sort("_id", -1))
    return render_template("dashboard.html", user=user, posts=all_posts)

# ================= LIKE POST =================
@app.route("/like/<post_id>")
def like_post(post_id):
    if not session.get("email"):
        return redirect("/")

    post = posts.find_one({"_id": ObjectId(post_id)})
    user_email = session["email"]

    if not post:
        return redirect("/dashboard")

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

# ================= DELETE POST =================
@app.route("/delete-post/<post_id>")
def delete_post(post_id):
    if not session.get("email"):
        return redirect("/")

    posts.delete_one({
        "_id": ObjectId(post_id),
        "email": session["email"]  # Only own post delete
    })

    return redirect("/dashboard")

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)