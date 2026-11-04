from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Customer, User
from app.repositories.address_repo import AddressRepository
from app.repositories.user_repo import UserRepository
from app.schemas.address import AddressCreateRequest, AddressResponse, AddressUpdateRequest
from app.schemas.user import CustomerProfileResponse, CustomerProfileUpdateRequest


class CustomerService:
    @staticmethod
    def get_profile(db: Session, user: User) -> CustomerProfileResponse:
        customer = db.query(Customer).filter(Customer.customer_id == user.user_id).first()
        loyalty = customer.loyalty_points if customer else 0
        pref = customer.dietary_preference.value if customer and hasattr(customer.dietary_preference, "value") else (str(customer.dietary_preference) if customer and customer.dietary_preference else "ALL")

        customer_dict = {
            "customer_id": user.user_id,
            "loyalty_points": loyalty,
            "dietary_preference": str(pref),
        }

        return CustomerProfileResponse(
            user_id=user.user_id,
            email=user.email,
            phone_number=user.phone_number,
            first_name=user.first_name,
            last_name=user.last_name,
            loyalty_points=loyalty,
            dietary_preference=str(pref),
            created_at=user.created_at,
            customer=customer_dict,
        )

    @staticmethod
    def update_profile(db: Session, user: User, data: CustomerProfileUpdateRequest) -> CustomerProfileResponse:
        # Check phone uniqueness if modified
        if data.phone_number is not None and data.phone_number.strip():
            phone_clean = data.phone_number.strip()
            if phone_clean != user.phone_number:
                existing = UserRepository.get_by_phone(db, phone_clean)
                if existing and existing.user_id != user.user_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="This phone number is already registered to another account",
                    )
                user.phone_number = phone_clean

        if data.first_name is not None and data.first_name.strip():
            user.first_name = data.first_name.strip()
        if data.last_name is not None and data.last_name.strip():
            user.last_name = data.last_name.strip()

        customer = db.query(Customer).filter(Customer.customer_id == user.user_id).first()
        if not customer:
            from app.models.user import DietaryPreference
            customer = Customer(
                customer_id=user.user_id,
                loyalty_points=0,
                dietary_preference=DietaryPreference.ALL,
            )
            db.add(customer)
            db.flush()

        if data.dietary_preference is not None:
            pref_val = data.dietary_preference.value if hasattr(data.dietary_preference, "value") else data.dietary_preference
            customer.dietary_preference = pref_val

        db.commit()
        db.refresh(user)
        db.refresh(customer)
        return CustomerService.get_profile(db, user)

    # Address Management
    @staticmethod
    def list_addresses(db: Session, customer_id: int) -> List[AddressResponse]:
        addresses = AddressRepository.get_customer_addresses(db, customer_id)
        return [AddressResponse.model_validate(a) for a in addresses]

    @staticmethod
    def add_address(db: Session, customer_id: int, data: AddressCreateRequest) -> AddressResponse:
        addr = AddressRepository.create_address(db, customer_id, data)
        return AddressResponse.model_validate(addr)

    @staticmethod
    def update_address(db: Session, customer_id: int, address_id: int, data: AddressUpdateRequest) -> AddressResponse:
        addr = AddressRepository.get_by_id_and_customer(db, address_id, customer_id)
        if not addr:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Delivery address not found or unauthorized",
            )
        updated = AddressRepository.update_address(db, addr, data)
        return AddressResponse.model_validate(updated)

    @staticmethod
    def delete_address(db: Session, customer_id: int, address_id: int) -> bool:
        addr = AddressRepository.get_by_id_and_customer(db, address_id, customer_id)
        if not addr:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Delivery address not found or unauthorized",
            )
        return AddressRepository.delete_address(db, addr)
