# TODO

- [ ] Monter un plan pour masquer sidebar/navbar quand `!user.is_authenticated`.
- [x] Mettre à jour `templates/base.html`:
  - [x] Encapsuler sidebar + layout `row/col` dans `{% if user.is_authenticated %}`
  - [x] Gérer le layout alternatif (login) sans sidebar
- [x] Améliorer `templates/registration/login.html` légèrement (sans refonte complète)
- [x] Tester : /login/, /logout/, connexion




