import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestprojet.settings')
django.setup()

from django.db import connection, ProgrammingError

print("🔧 Correction des contraintes...")

with connection.cursor() as cursor:
    # 1. Vérifier les codes vides dans projects_activity
    cursor.execute("SELECT id, project_id FROM projects_activity WHERE code = '' OR code IS NULL;")
    empty = cursor.fetchall()
    
    if empty:
        print("⚠️ Activités avec code vide:")
        for act_id, project_id in empty:
            new_code = f"A{project_id}_{act_id}"
            cursor.execute(
                "UPDATE projects_activity SET code = %s WHERE id = %s;",
                [new_code, act_id]
            )
            print(f"   ✅ Activité {act_id} → {new_code}")
    else:
        print("✅ Aucun code vide dans projects_activity")

    # 2. Ajouter la contrainte UNIQUE pour Activity
    try:
        cursor.execute("ALTER TABLE projects_activity ADD CONSTRAINT unique_project_code UNIQUE (project_id, code);")
        print("✅ Contrainte unique ajoutée sur (project_id, code)")
    except ProgrammingError as e:
        if 'already exists' in str(e).lower():
            print("⚠️ La contrainte existe déjà")
        else:
            print(f"❌ Erreur: {e}")

    # 3. Vérifier les contraintes
    cursor.execute("""
        SELECT constraint_name 
        FROM information_schema.table_constraints 
        WHERE table_name = 'projects_activity' 
        AND constraint_type = 'UNIQUE';
    """)
    activity_constraints = [row[0] for row in cursor.fetchall()]
    print("📋 Contraintes UNIQUE sur projects_activity:", activity_constraints)
    
    cursor.execute("""
        SELECT constraint_name 
        FROM information_schema.table_constraints 
        WHERE table_name = 'projects_subactivity' 
        AND constraint_type = 'UNIQUE';
    """)
    subactivity_constraints = [row[0] for row in cursor.fetchall()]
    print("📋 Contraintes UNIQUE sur projects_subactivity:", subactivity_constraints)

print("✅ Terminé !")