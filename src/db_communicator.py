import sqlite3
from sqlite3 import Error
from config import DB_URI, SIZES
import datetime
import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


class DBCommunicator:
    def __init__(self):
        self.connection = self.create_connection(f"./{DB_URI}")
        self.cursor = self.connection.cursor() if self.connection else None

        self.users_table = UsersTable(self.connection)
        self.checks_table = ChecksTable(self.connection)
        self.sizes_table = SizesTable(self.connection)

        self.create_tables()

    @staticmethod
    def create_connection(db_file):
        try:
            sqlite_connection = sqlite3.connect(db_file)
            cursor = sqlite_connection.cursor()
            logger.info("Database created and successfully connected to SQLite")
            sqlite_select_query = "select sqlite_version();"
            cursor.execute(sqlite_select_query)
            record = cursor.fetchall()
            logger.info(f"SQLite version: {record}")
            cursor.close()

        except sqlite3.Error as error:
            logger.info(f"Error creating SQLite database connection {error}")
        finally:
            if sqlite_connection:
                return sqlite_connection

    def create_tables(self):
        if not self.cursor:
            raise RuntimeError("No SQLite cursor available")

        self.users_table.create_table()
        self.checks_table.create_table()
        self.sizes_table.create_table()

        self.connection.commit()
        logger.info("All SQLite tables created successfully")


class UsersTable:
    def __init__(self, connection):
        self.connection = connection
        self.cursor = self.connection.cursor()

    def create_table(self):
        create_table_query = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            telegram_username VARCHAR NOT NULL,
            size_name VARCHAR,
            name TEXT,
            email VARCHAR,
            phone VARCHAR,
            delivery_type VARCHAR,
            address TEXT,
            postcode INTEGER,
            instagram VARCHAR
        );"""

        with self.connection:
            self.cursor.execute(create_table_query)
        logger.info("SQLite 'users' table created")

    def exists(self, user_id: int) -> bool:
        with self.connection:
            res = self.cursor.execute(
                "SELECT * FROM users WHERE user_id = :user_id", {"user_id": user_id}
            ).fetchmany(1)
        return len(res) != 0

    def add_user(
        self,
        user_id: int,
        telegram_username: str,
        size_name=None,
        name=None,
        email=None,
        phone=None,
        delivery_type=None,
        address=None,
        postcode=None,
        instagram=None,
    ):
        with self.connection:
            return self.cursor.execute(
                """INSERT INTO users 
                (user_id, telegram_username, size_name, name, email, phone, delivery_type, address, postcode, instagram) 
                VALUES 
                (:user_id, :telegram_username, :size_name, :name, :email, :phone, :delivery_type, :address, :postcode, :instagram)""",
                {
                    "user_id": user_id,
                    "telegram_username": telegram_username,
                    "size_name": size_name,
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "delivery_type": delivery_type,
                    "address": address,
                    "postcode": postcode,
                    "instagram": instagram,
                },
            )

    def update_user(self, user_id: int, field_name: str, field_value):
        with self.connection:
            return self.cursor.execute(
                f"UPDATE users SET {field_name} = :field_value WHERE user_id = :user_id",
                {
                    "user_id": user_id,
                    "field_value": field_value,
                },
            )

    def get(self, user_id: int):
        with self.connection:
            res = self.cursor.execute(
                "SELECT * FROM users WHERE user_id = :user_id", {"user_id": user_id}
            ).fetchmany(1)
        return (
            None
            if len(res) == 0
            else {
                "user_id": res[0][1],
                "telegram_username": res[0][2],
                "size_name": res[0][3],
                "name": res[0][4],
                "email": res[0][5],
                "phone": res[0][6],
                "delivery_type": res[0][7],
                "address": res[0][8],
                "postcode": res[0][9],
                "instagram": res[0][10],
            }
        )


class ChecksTable:
    def __init__(self, connection):
        self.connection = connection
        self.cursor = self.connection.cursor()

    def create_table(self):
        create_table_query = """
        CREATE TABLE IF NOT EXISTS checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            bill_id VARCHAR NOT NULL,
            comment VARCHAR NOT NULL,
            created_at VARCHAR NOT NULL,
            status VARCHAR NOT NULL DEFAULT 'UNPAID'
        );"""

        with self.connection:
            self.cursor.execute(create_table_query)
        logger.info("SQLite 'checks' table created")

    def add_check(self, user_id: int, amount: float, bill_id: str, comment: str):
        created_at = datetime.datetime.now().isoformat()
        with self.connection:
            return self.cursor.execute(
                """INSERT INTO checks (user_id, amount, bill_id, comment, created_at) 
                VALUES (:user_id, :amount, :bill_id, :comment, :created_at)""",
                {
                    "user_id": user_id,
                    "amount": amount,
                    "bill_id": bill_id,
                    "comment": comment,
                    "created_at": created_at,
                },
            )

    def get_check(self, bill_id: str):
        with self.connection:
            res = self.cursor.execute(
                "SELECT * FROM checks WHERE bill_id = :bill_id", {"bill_id": bill_id}
            ).fetchmany(1)
        return (
            None
            if len(res) == 0
            else {
                "user_id": res[0][1],
                "amount": res[0][2],
                "bill_id": res[0][3],
                "comment": res[0][4],
                "created_at": res[0][5],
                "status": res[0][6],
            }
        )

    def pay_check(self, bill_id):
        with self.connection:
            return self.cursor.execute(
                "UPDATE checks SET status = 'PAID' WHERE bill_id = :bill_id",
                {"bill_id": bill_id},
            )


class SizesTable:
    def __init__(self, connection):
        self.connection = connection
        self.cursor = self.connection.cursor()
        self.size_names = SIZES

    def create_table(self):
        create_table_query = """
        CREATE TABLE IF NOT EXISTS sizes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            size_name VARCHAR NOT NULL,
            in_stock INTEGER NOT NULL DEFAULT 0
        );"""

        with self.connection:
            self.cursor.execute(create_table_query)
            self.populate_table()
        logger.info("SQLite 'sizes' table created")

    def exists(self, size_name: str) -> bool:
        with self.connection:
            res = self.cursor.execute(
                "SELECT * FROM sizes WHERE size_name = :size_name",
                {"size_name": size_name},
            ).fetchmany(1)
        return len(res) != 0

    def populate_table(self):
        with self.connection:
            for size_name in self.size_names:
                if not self.exists(size_name):
                    self.cursor.execute(
                        "INSERT INTO sizes (size_name) VALUES (:size_name)",
                        {"size_name": size_name},
                    )

    def get_stock_data(self) -> dict:
        data = {}
        with self.connection:
            for size_name in self.size_names:
                res = self.cursor.execute(
                    "SELECT * FROM sizes WHERE size_name = :size_name",
                    {"size_name": size_name},
                ).fetchmany(1)
                if len(res) == 0:
                    raise RuntimeError(f"No {size_name} row in 'sizes' table")
                data[size_name] = res[0][2]
        return data

    def set_quantity(self, size_name: str, quantity: int):
        with self.connection:
            return self.cursor.execute(
                "UPDATE sizes SET in_stock = :quantity WHERE size_name = :size_name",
                {"quantity": quantity, "size_name": size_name},
            )


db = DBCommunicator()
