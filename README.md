# API Flask + Neo4j

Ce projet est une API RESTful développée avec **Flask** et connectée à une base de données **Neo4j** via `py2neo`. Elle permet de gérer des utilisateurs, des posts, des commentaires, des likes, et des relations d'amitié.

---

## 🌍 Fonctionnalités principales

- CRUD utilisateurs
- CRUD posts liés aux utilisateurs
- Commentaires liés aux posts et aux utilisateurs
- Likes sur posts et commentaires
- Relations d'amitié entre utilisateurs (symétriques)
- Recherche d'amis en commun

---

## ⚙️ Installation

1. **Cloner le dépôt**

```bash
git clone https://github.com/Fulvail/flask-neo4j.api.git
cd flask-neo4j.api
