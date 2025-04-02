import json
from datetime import date, timedelta
from typing import List, Optional
from datetime import datetime
from src.schemas import ContactModel, ContactResponse

import os

DATA_FILE = os.path.join('storage', 'data.json')

class ContactRepository:
    def __init__(self):
        self.data_file = DATA_FILE

    def _load_data(self) -> List[dict]:
        try:
            with open(self.data_file, 'r') as file:
                data = json.load(file)
        except json.JSONDecodeError:
            print("Файл пустий або містить некоректний JSON.")
            data = []

        return data

    def _save_data(self, data):
        with open(self.data_file, 'w') as file:
            json.dump(data, file, default=self._default_converter)

    @staticmethod
    def _default_converter(o):
        if isinstance(o, date):
            return o.isoformat()
        raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

    async def get_contacts(
            self, name: str, surname: str, email: str, skip: int, limit: int
    ) -> List[ContactModel]:
        data = self._load_data()
        filtered = [
            ContactResponse.parse_obj(item) for item in data
            if name in item['name'] and surname in item['surname'] and email in item['email']
        ]
        return filtered[skip:skip + limit]

    async def get_contact_by_id(self, contact_id: int) -> Optional[ContactModel]:
        data = self._load_data()
        contact = next((item for item in data if item['id'] == contact_id), None)
        return ContactResponse.parse_obj(contact) if contact else None

    async def create_contact(self, body: ContactModel) -> ContactModel:
        data = self._load_data()
        contact = body.dict()
        contact['id'] = max(item['id'] for item in data) + 1 if data else 1
        contact['created_at'] = datetime.now().isoformat()
        contact['updated_at'] = datetime.now().isoformat()
        data.append(contact)
        self._save_data(data)
        return ContactResponse.parse_obj(contact)

    async def update_contact(
            self, contact_id: int, body: ContactModel
    ) -> Optional[ContactModel]:
        data = self._load_data()
        contact = next((item for item in data if item['id'] == contact_id), None)
        if contact:
            for key, value in body.dict(exclude_unset=True).items():
                contact[key] = value
            self._save_data(data)
            return ContactResponse.parse_obj(contact)
        return None

    async def remove_contact(self, contact_id: int) -> Optional[ContactModel]:
        data = self._load_data()
        new_data = [item for item in data if item['id'] != contact_id]
        if len(data) != len(new_data):
            self._save_data(new_data)
            return ContactResponse.parse_obj(next(item for item in data if item['id'] == contact_id))
        return None

    async def is_contact_exists(self, email: str, phone: str) -> bool:
        data = self._load_data()
        return any(item['email'] == email or item['phone'] == phone for item in data)

    async def get_upcoming_birthdays(self, days: int) -> list[ContactModel]:
        today = date.today()
        end_date = today + timedelta(days=days)
        data = self._load_data()
        upcoming = [
            ContactResponse.parse_obj(item) for item in data
            if today <= date.fromisoformat(item['birthday']) <= end_date
        ]
        return sorted(upcoming, key=lambda x: x.birthday)
