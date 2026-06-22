# TODO

- [ ] Fix NoReverseMatch in templates/projects/admin/subactivity_form.html (wrong URL argument: empty project.pk)
- [ ] Ensure AdminSubActivityCreateView provides `form.instance.activity.project.pk` on GET by setting instance.activity (and activity.project) and/or activity FK correctly in get_form_kwargs
- [ ] Run Django server / quick check by visiting the create URL

