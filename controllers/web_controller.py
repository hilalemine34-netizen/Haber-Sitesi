from flask import (
    Flask,
    render_template,
    abort,
    request,
    redirect,
    url_for,
    session,
    flash,
)

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


from repositories.news_repository import NewsRepository
from repositories.interaction_repo import InteractionRepository
from repositories.user_repository import UserRepository
from controllers.notification_service import NotificationService
from services.filter_engine import FilterEngine

from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder="../templates", static_folder="../static")
app.secret_key = "supersecretkey"

news_repo = NewsRepository()
interaction_repo = InteractionRepository()
user_repo = UserRepository()


def is_logged_in():
    return session.get("user_id") is not None


#  LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    logger.info("LOGIN sayfası açıldı")

    if request.method == "POST":
        logger.info("POST login isteği geldi")
        username = request.form.get("username")
        password = request.form.get("password")

        logger.info(f"Giriş denemesi: {username}")

        user = user_repo.get_user_by_username(username)

        if user and user.check_password(password):
            session["user_id"] = user.id
            session["username"] = user.username
            logger.info(f"Giriş başarılı user_id={user.id}")
            flash(" Giriş başarılı", "success")
            return redirect(url_for("home"))

        logger.warning("Hatalı giriş")
        flash(" Kullanıcı adı veya şifre hatalı", "error")
        return redirect(url_for("login"))

    return render_template("login.html")


#  REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():
    logger.info("REGISTER sayfası açıldı")

    if request.method == "POST":
        logger.info("Register POST geldi")
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if not username or not email or not password:
            logger.warning("Eksik form")
            flash(" Tüm alanları doldurun", "error")
            return redirect(url_for("register"))

        if user_repo.get_user_by_username(username):
            flash(" Bu kullanıcı zaten var", "error")
            return redirect(url_for("register"))

        password_hash = generate_password_hash(password)
        user_repo.create_user(username, email, password_hash)

        logger.info(f"Yeni kullanıcı oluşturuldu: {username}")
        flash(" Kayıt başarılı", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


#  LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    flash(" Çıkış yapıldı", "success")
    return redirect(url_for("login"))


#  SETTINGS
@app.route("/settings", methods=["GET", "POST"])
def settings():
    if not is_logged_in():
        return redirect(url_for("login"))

    if request.method == "POST":
        selected_categories = request.form.getlist("categories")
        user_repo.update_preferences(session["user_id"], selected_categories)
        flash(" Tercihler güncellendi", "success")
        return redirect(url_for("settings"))

    return render_template(
        "settings.html",
        categories=news_repo.get_all_categories(),
        user_categories=user_repo.get_user_categories(session["user_id"])
    )


#  HOME 
@app.route("/")
def home():
    if not is_logged_in():
        return redirect(url_for("login"))

    category = request.args.get("category")
    logger.info(f"Kategori filtre: {category}")

    articles = news_repo.get_all_articles(category=category)
    trending_articles = news_repo.get_trending_articles()

    return render_template(
        "index.html",
        articles=articles,
        trending_articles=trending_articles,
        breaking_news=articles[0] if articles else None,
        active_cat=category if category else "all"
    )


#  MY FEED
@app.route("/my-feed")
def my_feed():
    if not is_logged_in():
        return redirect(url_for("login"))

    user_id = session["user_id"]
    logger.info(f"My-feed açıldı user_id={user_id}")

    cats = user_repo.get_user_categories(user_id)
    articles = news_repo.get_articles_by_multiple_categories(cats) if cats else news_repo.get_all_articles()

    return render_template(
        "index.html",
        articles=articles,
        trending_articles=[],
        breaking_news=articles[0] if articles else None,
        active_cat="my_feed"
    )


#  RECOMMENDATION
@app.route("/recommendations")
def recommendations():
    if not is_logged_in():
        return redirect(url_for("login"))

    user_id = session["user_id"]
    logger.info(f"Recommendation çağrıldı user_id={user_id}")

    engine = FilterEngine(interaction_repo, news_repo)
    articles = engine.recommend(user_id)

    if not articles:
        logger.info("Cold start kullanıldı")
        articles = engine.cold_start()

    return render_template(
        "index.html",
        articles=articles,
        trending_articles=[],
        breaking_news=articles[0] if articles else None,
        active_cat="recommendations",
        page_title="🎯 Sana Özel"
    )


#  ARTICLE DETAIL
@app.route("/article/<int:id>")
def article_detail(id):
    if not is_logged_in():
        return redirect(url_for("login"))

    logger.info(f"Article açıldı id={id}")

    article = news_repo.get_article_by_id(id)
    if not article:
        abort(404)

    interaction_repo.add_view(session["user_id"], id)

    return render_template(
        "article_detail.html",
        article=article,
        comments=interaction_repo.get_comments_by_article(id),
        view_count=interaction_repo.get_view_count(id)
    )


#  LIKE
@app.route("/like/<int:id>")
def like(id):
    if not is_logged_in():
        return redirect(url_for("login"))

    logger.info(f"Like atıldı user_id={session.get('user_id')} article_id={id}")
    interaction_repo.add_like(session["user_id"], id)
    return redirect(request.referrer or url_for("home"))


#  FAVORITE
@app.route("/add_favorite/<int:id>")
def add_favorite(id):
    if not is_logged_in():
        return redirect(url_for("login"))

    logger.info(f"Favori eklendi user_id={session.get('user_id')} article_id={id}")
    interaction_repo.add_favorite(session["user_id"], id)
    return redirect(request.referrer or url_for("home"))


#  LIKED
@app.route("/liked-articles")
def liked_articles():
    if not is_logged_in():
        return redirect(url_for("login"))

    user_id = session["user_id"]   

    articles = news_repo.get_liked_articles(user_id)

    return render_template(
        "index.html",
        articles=articles,
        trending_articles=[],
        breaking_news=None,
        active_cat="liked"
    )


#  FAVORITES
@app.route("/favorites")
def favorites():
    if not is_logged_in():
        return redirect(url_for("login"))

    logger.info(f"Favoriler açıldı user_id={session.get('user_id')}")

    articles = interaction_repo.get_user_favorites(session["user_id"])

    return render_template(
        "index.html",
        articles=articles,
        trending_articles=[],
        breaking_news=None,
        active_cat="favorites"
    )


#  SEARCH
@app.route("/search")
def search():
    if not is_logged_in():
        return redirect(url_for("login"))

    q = request.args.get("q", "").strip()
    logger.info(f"Search: {q}")

    if not q:
        return redirect(url_for("home"))

    articles = news_repo.search_articles(q)

    return render_template(
        "index.html",
        articles=articles,
        trending_articles=[],
        breaking_news=None,
        active_cat="search"
    )


#  NOTIFICATIONS
@app.route("/notifications")
def notifications():
    if not is_logged_in():
        return redirect(url_for("login"))

    logger.info(f"Notifications çağrıldı user_id={session.get('user_id')}")

    service = NotificationService(news_repo, interaction_repo, user_repo)

    return render_template(
        "notifications.html",
        notifications=service.get_user_notifications(session["user_id"]),
        trending=service.get_trending_alert()
    )


#  NOTIFICATION COUNT
@app.route("/notification-count")
def notification_count():
    if not is_logged_in():
        return {"count": 0}

    service = NotificationService(news_repo, interaction_repo, user_repo)
    notifications = service.get_user_notifications(session["user_id"])

    return {"count": len(notifications)}

#  COMMENT
@app.route("/add_comment", methods=["POST"])
def add_comment():
    if not is_logged_in():
        return redirect(url_for("login"))

    article_id = request.form.get("article_id")
    content = request.form.get("content")

    logger.info(f"Yorum eklendi article_id={article_id}")

    user = user_repo.get_user_by_id(session["user_id"])

    interaction_repo.add_comment(
        session["user_id"],
        article_id,
        content,
        user.username
    )

    return redirect(url_for("article_detail", id=article_id))


@app.route("/check-new-articles")
def check_new_articles():
    user_id = session.get("user_id", 0)
    last_seen_id = session.get("last_seen_id", 0)

    service = NotificationService(news_repo, interaction_repo, user_repo)
    has_new = service.has_new_articles(last_seen_id)

    return {"has_new": has_new}