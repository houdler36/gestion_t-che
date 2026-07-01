# TODO (mise à jour filtre DailyLogCreateView)

- [x] Comprendre le code existant dans `gestprojet/tracking/views.py`
- [x] Déplacer le filtrage du queryset `task` de `form_valid()` vers `get_form()` pour que le filtre s’applique lors du rendu
- [x] Vérifier le rendu UI (liste déroulante) sur `/tracking/log/create/` (à valider côté navigateur)
- [ ] Vérifier que l’ajout d’un DailyLog enregistre bien et redirige vers `tracking:log_list`


