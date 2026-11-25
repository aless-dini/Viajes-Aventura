"""Answer the ten validation questions on the database configured in .env.

Load the sample data first:  python init_db.py --seed
Then run:                    python validate_db.py
"""

from persistence.database import DatabaseError, create_database
from persistence.validation_queries import QUESTIONS, run_question


def main():
    try:
        db = create_database()
        print(f"Base de datos: {db.describe()}")
        for question in QUESTIONS:
            columns, rows = run_question(db, question)
            print(f"\n{question['number']}. {question['question']}")
            if question["params"]:
                print(f"   Parámetros: {question['params']}")
            print("   " + " | ".join(columns))
            for row in rows:
                print("   " + " | ".join("-" if value is None else str(value) for value in row))
    except DatabaseError as error:
        print(f"Error: {error}")


if __name__ == "__main__":
    main()
