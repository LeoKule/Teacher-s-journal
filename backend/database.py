from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Строка подключения (убедись, что пароль актуальный)
DATABASE_URL = "mysql+pymysql://teacher_app:my_secure_password@127.0.0.1:3306/teacher_journal"

# Движок базы данных
engine = create_engine(DATABASE_URL, echo=True)

# Фабрика сессий. Сессия — это транзакция, через которую мы будем отправлять
# и получать данные из базы при каждом запросе пользователя.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс, от которого будут наследоваться все наши модели (таблицы)
Base = declarative_base()