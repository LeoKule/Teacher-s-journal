from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import get_settings

# Загружаем конфигурацию из .env
settings = get_settings()

# Движок базы данных
engine = create_engine(settings.DATABASE_URL, echo=settings.DEBUG)

# Фабрика сессий. Сессия — это транзакция, через которую мы будем отправлять
# и получать данные из базы при каждом запросе пользователя.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс, от которого будут наследоваться все наши модели (таблицы)
Base = declarative_base()