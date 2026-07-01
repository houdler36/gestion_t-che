# TODO — Passage de “heures” à “présence”

- [ ] Modifier `tracking/models.py` : supprimer `time_spent` et `time_spent_minutes` ; la présence est implicite (un log = présent).
- [ ] Créer migration `tracking`.
- [ ] Modifier `tracking/admin.py` : retirer champs d’heures et les colonnes d’affichage.
- [ ] Modifier `templates/tracking/log_list.html` : remplacer la colonne “Temps passé” par “Présent”.
- [ ] Modifier `reports/monthly_views.py` : remplacer toutes les agrégations basées sur minutes/heures par des comptes de jours distincts (présence).
- [ ] Modifier `reports/weekly_views.py` : idem pour la semaine.
- [ ] Modifier `templates/reports/monthly_report_dashboard.html` : renommer `Total heures` -> `Jours travaillés`, supprimer colonnes/éléments “Heures”.
- [ ] Modifier `templates/reports/weekly_report_dashboard.html` : renommer `Total heures` -> `Jours travaillés`, supprimer colonne/éléments “Heures”.
- [ ] Modifier `export_monthly_report_csv` et `export_weekly_report_csv` : colonnes “Heures” -> “Jours travaillés/Présence”.
- [ ] Supprimer l’usage de `d.hours` dans les vues détaillées et templates.
- [ ] Exécuter `python manage.py makemigrations` + `migrate`.
- [ ] Lancer `python manage.py test` + vérifier pages rapports/tracking.

