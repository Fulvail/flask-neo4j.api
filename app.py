from flask import Flask, jsonify, request
from py2neo import Graph, Node, Relationship
from datetime import datetime
import uuid

app = Flask(__name__)
graph = Graph("bolt://localhost:7687", auth=("neo4j", "password"))

@app.route("/")
def home():
    return jsonify({"message": "API Neo4j Flask opérationnelle 🚀"})

# --- UTILISATEURS ---
@app.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    if not name or not email:
        return jsonify({"error": "name et email requis"}), 400

    user_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    user = Node("User", id=user_id, name=name, email=email, created_at=created_at)
    graph.create(user)
    return jsonify({"message": "Utilisateur créé avec succès", "id": user_id}), 201

@app.route("/users", methods=["GET"])
def get_users():
    users = graph.run("MATCH (u:User) RETURN u").data()
    result = []
    for record in users:
        user = record["u"]
        result.append({
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "created_at": user["created_at"]
        })
    return jsonify(result), 200

@app.route("/users/<user_id>", methods=["GET"])
def get_user_by_id(user_id):
    user = graph.evaluate("MATCH (u:User {id: $id}) RETURN u", id=user_id)
    if user is None:
        return jsonify({"error": "Utilisateur non trouvé"}), 404
    return jsonify({
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "created_at": user["created_at"]
    }), 200

# --- POSTS ---
@app.route("/users/<user_id>/posts", methods=["POST"])
def create_post(user_id):
    user = graph.evaluate("MATCH (u:User {id: $id}) RETURN u", id=user_id)
    if user is None:
        return jsonify({"error": "Utilisateur non trouvé"}), 404

    data = request.get_json()
    title = data.get("title")
    content = data.get("content")
    if not title or not content:
        return jsonify({"error": "title et content requis"}), 400

    post_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    post = Node("Post", id=post_id, title=title, content=content, created_at=created_at)
    graph.create(post)
    graph.create(Relationship(user, "CREATED", post))

    return jsonify({"message": "Post créé avec succès", "id": post_id}), 201

@app.route("/posts", methods=["GET"])
def get_all_posts():
    posts = graph.run("MATCH (p:Post) RETURN p").data()
    result = []
    for record in posts:
        post = record["p"]
        result.append({
            "id": post["id"],
            "title": post["title"],
            "content": post["content"],
            "created_at": post["created_at"]
        })
    return jsonify(result), 200

@app.route("/users/<user_id>/posts", methods=["GET"])
def get_user_posts(user_id):
    posts = graph.run("""
        MATCH (u:User {id: $id})-[:CREATED]->(p:Post)
        RETURN p
    """, id=user_id).data()

    result = []
    for record in posts:
        post = record["p"]
        result.append({
            "id": post["id"],
            "title": post["title"],
            "content": post["content"],
            "created_at": post["created_at"]
        })
    return jsonify(result), 200

# --- COMMENTAIRES ---
@app.route("/posts/<post_id>/comments", methods=["POST"])
def create_comment(post_id):
    post = graph.evaluate("MATCH (p:Post {id: $id}) RETURN p", id=post_id)
    if post is None:
        return jsonify({"error": "Post non trouvé"}), 404

    data = request.get_json()
    user_id = data.get("user_id")
    content = data.get("content")
    if not user_id or not content:
        return jsonify({"error": "user_id et content requis"}), 400

    user = graph.evaluate("MATCH (u:User {id: $id}) RETURN u", id=user_id)
    if user is None:
        return jsonify({"error": "Utilisateur non trouvé"}), 404

    comment_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    comment = Node("Comment", id=comment_id, content=content, created_at=created_at)
    graph.create(comment)
    graph.create(Relationship(user, "CREATED", comment))
    graph.create(Relationship(post, "HAS_COMMENT", comment))

    return jsonify({"message": "Commentaire ajouté", "id": comment_id}), 201

@app.route("/posts/<post_id>/comments", methods=["GET"])
def get_comments_for_post(post_id):
    comments = graph.run("""
        MATCH (p:Post {id: $id})-[:HAS_COMMENT]->(c:Comment)
        RETURN c
    """, id=post_id).data()

    result = []
    for record in comments:
        comment = record["c"]
        result.append({
            "id": comment["id"],
            "content": comment["content"],
            "created_at": comment["created_at"]
        })
    return jsonify(result), 200

# --- AMITIES ---
@app.route("/users/<user_id>/friends", methods=["GET"])
def get_user_friends(user_id):
    friends = graph.run("""
        MATCH (u:User {id: $id})-[:FRIENDS_WITH]-(f:User)
        RETURN f
    """, id=user_id).data()

    result = []
    for record in friends:
        f = record["f"]
        result.append({
            "id": f["id"],
            "name": f["name"],
            "email": f["email"],
            "created_at": f["created_at"]
        })
    return jsonify(result), 200

@app.route("/users/<user_id>/friends", methods=["POST"])
def add_friend(user_id):
    data = request.get_json()
    friend_id = data.get("friend_id")
    if not friend_id:
        return jsonify({"error": "friend_id requis"}), 400

    user = graph.evaluate("MATCH (u:User {id: $id}) RETURN u", id=user_id)
    friend = graph.evaluate("MATCH (u:User {id: $id}) RETURN u", id=friend_id)

    if not user or not friend:
        return jsonify({"error": "Utilisateur ou ami non trouvé"}), 404

    graph.run("""
        MATCH (a:User {id: $id1}), (b:User {id: $id2})
        MERGE (a)-[:FRIENDS_WITH]-(b)
    """, id1=user_id, id2=friend_id)

    return jsonify({"message": "Amitié ajoutée"}), 200

@app.route("/users/<user_id>/friends/<friend_id>", methods=["DELETE"])
def remove_friend(user_id, friend_id):
    graph.run("""
        MATCH (a:User {id: $id1})-[f:FRIENDS_WITH]-(b:User {id: $id2})
        DELETE f
    """, id1=user_id, id2=friend_id)

    return jsonify({"message": "Amitié supprimée"}), 200

@app.route("/users/<user_id>/friends/<friend_id>", methods=["GET"])
def are_friends(user_id, friend_id):
    rel = graph.evaluate("""
        MATCH (a:User {id: $id1})-[:FRIENDS_WITH]-(b:User {id: $id2})
        RETURN a
    """, id1=user_id, id2=friend_id)

    return jsonify({"are_friends": bool(rel)}), 200

@app.route("/users/<user_id>/mutual-friends/<other_id>", methods=["GET"])
def get_mutual_friends(user_id, other_id):
    mutuals = graph.run("""
        MATCH (a:User {id: $id1})-[:FRIENDS_WITH]-(m:User)-[:FRIENDS_WITH]-(b:User {id: $id2})
        RETURN DISTINCT m
    """, id1=user_id, id2=other_id).data()

    result = []
    for record in mutuals:
        m = record["m"]
        result.append({
            "id": m["id"],
            "name": m["name"],
            "email": m["email"],
            "created_at": m["created_at"]
        })
    return jsonify(result), 200

if __name__ == "__main__":
    app.run(debug=True)