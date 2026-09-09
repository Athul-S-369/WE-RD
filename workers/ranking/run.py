from weird.pipeline.editorial import select_edition_stories
from weird.db import get_session_factory, init_db
from weird.models import Story


def main():
    init_db()
    session = get_session_factory()()
    try:
        stories = session.query(Story).all()
        selected = select_edition_stories(stories)
        print([(section, story.slug) for section, story, _featured in selected])
    finally:
        session.close()


if __name__ == "__main__":
    main()
