import random
from faker import Faker

class ProductGenerator:
    def __init__(self):
        self.categories = ['Elektronika', 'Nabiał', 'Narzędzia']
        self.fake = Faker('pl_PL')
        Faker.seed(42)
        random.seed(42)

    def _gen_attributes(self, category):
        """Generuje unikalny 'gulasz atrybutów' dla kategorii."""
        if category == 'Elektronika':
            return {
                "ram_gb": random.choice([8, 16, 32, 64]),
                "cpu": {
                    "producent": self.fake.company(),
                    "taktowanie": str(random.uniform(1, 5)) + " GHz",
                    "gamingowy": self.fake.boolean()
                },
                "grafika": f"Nvidia {self.fake.word().capitalize()} RTX",
                "porty": [self.fake.word() for _ in range(random.randint(1, 4))],
                "gwarancja": {"typ": "door-to-door", "miesiace": 24}
            }
        elif category == 'Nabiał':
            return {
                "tluszcz_procent": round(random.uniform(0, 40), 1),
                "cukier_g": random.randint(0, 50),
                "bakterie_lct": [self.fake.word() for _ in range(2)],
                "bio": self.fake.boolean(),
                "data_waznosci": self.fake.future_date().isoformat(),
                "producent": self.fake.company(),
                '"wysoko proteinowy"': self.fake.boolean()
            }
        elif category == 'Narzędzia':
            return {
                "obroty_max": random.randint(500, 5000),
                "udar": self.fake.boolean(),
                "producent_szczotek": self.fake.company(),
                "zasilanie": random.choice(["Akumulator", "Sieciowe", "Atom", "Chomki"]),
                "certyfikaty": [
                    {"kod": self.fake.ean8(), "data": self.fake.past_date().isoformat()}
                    for _ in range(random.randint(1, 3))
                ]
            }
        raise ValueError("Unknown categeory: " + category)

    def generate_batch(self, size=1000):
        """Tworzy paczkę danych gotową do wysyłki do bazy."""
        batch = []
        for _ in range(size):
            cat = random.choice(self.categories)
            product = {
                "nazwa": f"{self.fake.word().capitalize()} {self.fake.last_name()}",
                "kategoria": cat,
                "cena": float(self.fake.pydecimal(left_digits=4, right_digits=2, positive=True)),
                "atrybuty": self._gen_attributes(cat)
            }
            batch.append(product)
        return batch
