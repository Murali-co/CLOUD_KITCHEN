from typing import Optional
from sqlalchemy.orm import Session
from app.models import User, Customer, UserRole


class UserRepository:
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.user_id == user_id).first()

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email.lower().strip()).first()

    @staticmethod
    def get_by_phone(db: Session, phone: str) -> Optional[User]:
        return db.query(User).filter(User.phone_number == phone.strip()).first()

    @staticmethod
    def create_customer(
        db: Session,
        email: str,
        phone_number: str,
        password_hash: str,
        first_name: str,
        last_name: str,
    ) -> User:
        user = User(
            email=email.lower().strip(),
            phone_number=phone_number.strip(),
            password_hash=password_hash,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            role=UserRole.CUSTOMER,
            is_active=True,
        )
        db.add(user)
        db.flush()

        customer = Customer(
            customer_id=user.user_id,
            loyalty_points=0,
            dietary_preference="ALL",
        )
        db.add(customer)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_password(db: Session, user: User, new_hash: str) -> User:
        user.password_hash = new_hash
        db.commit()
        db.refresh(user)
        return user
