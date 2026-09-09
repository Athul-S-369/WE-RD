from weird.pipeline.analyze import enrich_stories
from weird.db import get_session_factory, init_db


def main():
    init_db()
    session = get_session_factory()()
    try:
        print(enrich_stories(session))
        session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    main()
