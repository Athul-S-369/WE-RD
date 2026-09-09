from weird.pipeline.process import process_articles
from weird.db import get_session_factory, init_db


def main():
    init_db()
    session = get_session_factory()()
    try:
        print(process_articles(session))
        session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    main()
