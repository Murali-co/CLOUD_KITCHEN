from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Address
from app.schemas.address import AddressCreateRequest, AddressUpdateRequest


class AddressRepository:
    @staticmethod
    def get_customer_addresses(db: Session, customer_id: int) -> List[Address]:
        return (
            db.query(Address)
            .filter(Address.customer_id == customer_id)
            .order_by(Address.is_default.desc(), Address.address_id.desc())
            .all()
        )

    @staticmethod
    def get_by_id_and_customer(db: Session, address_id: int, customer_id: int) -> Optional[Address]:
        return (
            db.query(Address)
            .filter(Address.address_id == address_id, Address.customer_id == customer_id)
            .first()
        )

    @staticmethod
    def create_address(db: Session, customer_id: int, data: AddressCreateRequest) -> Address:
        # If this is set to default, clear previous default
        if data.is_default:
            db.query(Address).filter(Address.customer_id == customer_id).update({"is_default": False})

        address = Address(
            customer_id=customer_id,
            address_label=data.address_label,
            recipient_name=data.recipient_name,
            recipient_phone=data.recipient_phone,
            address_line1=data.address_line1,
            address_line2=data.address_line2,
            landmark=data.landmark,
            city=data.city,
            state=data.state,
            postal_code=data.postal_code,
            latitude=data.latitude,
            longitude=data.longitude,
            is_default=data.is_default,
        )
        db.add(address)
        db.commit()
        db.refresh(address)
        return address

    @staticmethod
    def update_address(db: Session, address: Address, data: AddressUpdateRequest) -> Address:
        update_dict = data.model_dump(exclude_unset=True)
        if update_dict.get("is_default") is True:
            db.query(Address).filter(Address.customer_id == address.customer_id).update({"is_default": False})

        for key, val in update_dict.items():
            setattr(address, key, val)

        db.commit()
        db.refresh(address)
        return address

    @staticmethod
    def delete_address(db: Session, address: Address) -> bool:
        db.delete(address)
        db.commit()
        return True
