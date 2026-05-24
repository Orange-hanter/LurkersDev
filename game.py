import random
import math
from typing import List, Optional

# ---------------------- Helper classes ----------------------
class Staff:
    def __init__(self, skill: int, salary: int):
        self.skill = skill
        self.max_stamina = 100
        self.stamina = self.max_stamina
        self.salary = salary
        self.busy_timer = 0          # ticks remaining until free
        self.forced_rest = False     # True when stamina == 0

    @property
    def is_free(self) -> bool:
        """Staff can be assigned only if not forced to rest and not serving."""
        return not self.forced_rest and self.busy_timer == 0

    def start_service(self, base_stamina_drain: int = 10):
        """Begin serving a guest: set busy timer and drain stamina."""
        if not self.is_free or self.stamina <= 0:
            raise RuntimeError("Staff is not available")
        self.busy_timer = 1          # service always takes 1 tick
        self.stamina -= base_stamina_drain
        if self.stamina <= 0:
            self.stamina = 0
            self.forced_rest = True   # out of stamina → never available again

    def tick_update(self):
        """Called every tick to advance internal timers."""
        if self.forced_rest:
            # Already exhausted, nothing changes
            return
        if self.busy_timer > 0:
            self.busy_timer -= 1
        # If stamina == 0 but not forced_rest yet, force rest now
        if self.stamina == 0:
            self.forced_rest = True
            self.busy_timer = 0      # cancel any ongoing task (shouldn't happen)

class Guest:
    def __init__(self, budget: float, patience: int, expectation: float, mood: int):
        self.budget = budget
        self.patience = patience
        self.expectation = expectation
        self.mood = mood
        self.wait_timer = 0

class GameState:
    def __init__(self):
        self.budget = 200.0
        self.reputation = 0.0
        # Equipment qualities (0 – none, 1 – cheap, 3 – normal, 5 – expensive)
        self.kitchen_q = 0
        self.hall_q = 0
        self.staff_list: List[Staff] = []
        self.guest_queue: List[Guest] = []
        self.tick = 0

    @property
    def equipment_quality(self) -> float:
        """Average quality of kitchen and hall equipment."""
        return (self.kitchen_q + self.hall_q) / 2.0

    def hire_staff(self, skill: int, salary: int):
        self.staff_list.append(Staff(skill, salary))

    def fire_staff(self, index: int):
        if 0 <= index < len(self.staff_list):
            self.staff_list.pop(index)

# ---------------------- Game logic ----------------------
def spawn_guest(state: GameState):
    """Attempt to spawn a new guest based on current reputation."""
    base_rate = 0.5
    time_mult = 1.0      # no time-of-day effect for simplicity
    mult = 1 + state.reputation * 0.01
    if mult < 0.1:
        mult = 0.1
    spawn_chance = base_rate * mult * time_mult * random.uniform(0.8, 1.2)
    if random.random() < spawn_chance:
        # Generate guest parameters
        budget = max(5.0, random.gauss(40, 15))   # avoid negative
        patience = random.randint(3, 8)
        base_exp = 3.0
        expectation = base_exp + state.reputation * 0.05
        mood = random.randint(1, 10)
        state.guest_queue.append(Guest(budget, patience, expectation, mood))
        return True
    return False

def process_tick(state: GameState) -> List[str]:
    """Execute one full tick, return a list of event messages."""
    events = []
    state.tick += 1
    events.append(f"--- Tick {state.tick} ---")

    # 1. Check bankruptcy condition
    if state.reputation < 0:
        events.append("💥 Ваша репутация опустилась ниже нуля! Банкротство.")
        return events

    # 2. Update all staff members
    for i, staff in enumerate(state.staff_list):
        staff.tick_update()
        if staff.forced_rest:
            events.append(f"⚙️ Персонал #{i+1} выдохся и больше не может работать.")

    # 3. Spawn new guest
    if spawn_guest(state):
        events.append("🎲 Появился новый гость!")

    # 4. Assign free staff to waiting guests
    free_staff = [s for s in state.staff_list if s.is_free]
    # Assign in queue order (FIFO)
    while free_staff and state.guest_queue:
        staff = free_staff.pop(0)
        guest = state.guest_queue.pop(0)

        # Calculate quality
        quality = staff.skill * 0.7 + state.equipment_quality * 0.3
        staff.start_service(base_stamina_drain=10)

        if quality >= guest.expectation:
            income = guest.budget * 1.2
            state.budget += income
            state.reputation += 3
            events.append(f"😊 Успешное обслуживание! Заработано ${income:.2f}, репутация +3.")
        else:
            # Failure: refund + compensation
            loss = guest.budget  # just refunding the budget as penalty
            state.budget -= loss
            state.reputation -= 10
            events.append(f"😞 Провал! Гость недоволен, возврат ${loss:.2f}, репутация -10.")

    # 5. Handle waiting guests that were not assigned
    still_waiting = list(state.guest_queue)   # copy because we might modify
    for guest in still_waiting:
        guest.wait_timer += 1
        if guest.wait_timer >= guest.patience:
            state.guest_queue.remove(guest)
            state.reputation -= 5
            events.append(f"😤 Гость ушёл из-за долгого ожидания. Репутация -5.")

    # 6. Pay salaries to all staff
    total_salary = sum(s.salary for s in state.staff_list)
    state.budget -= total_salary
    events.append(f"💼 Зарплаты: -${total_salary:.2f}.")

    # Final status line
    events.append(f"💰 Бюджет: ${state.budget:.2f} | ⭐ Репутация: {state.reputation} | 👥 Гостей в очереди: {len(state.guest_queue)}")
    return events

# ---------------------- User interface ----------------------
def choose_equipment():
    """Initial equipment buying for kitchen and hall."""
    tiers = {
        '1': ('🟢 Дешёвое', 30, 1),
        '2': ('🟡 Нормальное', 60, 3),
        '3': ('🔴 Дорогое', 100, 5)
    }
    print("\n🛒 Магазин оснащения. Выберите уровень оборудования для кухни и зала.")
    for k, (name, price, q) in tiers.items():
        print(f"  {k}. {name}: ${price} (Quality +{q})")

    def pick(slot_name):
        while True:
            choice = input(f"Уровень для {slot_name} (1-3): ").strip()
            if choice in tiers:
                return tiers[choice]
            print("Неверный выбор.")

    k_name, k_price, k_q = pick("кухни")
    h_name, h_price, h_q = pick("зала")
    return (k_q, k_price), (h_q, h_price)

def hire_menu(state: GameState):
    """Let player hire staff with random skill and proportional salary."""
    print("\n👥 Найм персонала.")
    while True:
        # Generate a random candidate
        skill = random.randint(1, 10)
        salary = skill * 5   # $5 per skill point per tick
        print(f"Кандидат: Навык={skill}, Зарплата=${salary}/тик.")
        ans = input("Нанять? (y/n/stop): ").strip().lower()
        if ans == 'y':
            if state.budget < salary:
                print("Недостаточно бюджета для зарплаты этого сотрудника!")
            else:
                state.hire_staff(skill, salary)
                print(f"Сотрудник нанят! Персонал: {len(state.staff_list)} чел.")
        elif ans == 'stop':
            break
        else:
            continue
        if input("Нанять ещё? (y/n): ").strip().lower() != 'y':
            break

def shop_menu(state: GameState):
    """Upgrade equipment between ticks."""
    tiers = {
        '1': ('🟢 Дешёвое', 30, 1),
        '2': ('🟡 Нормальное', 60, 3),
        '3': ('🔴 Дорогое', 100, 5)
    }
    print("\n🛒 Обновление оборудования.")
    print("Текущее: Кухня Quality =", state.kitchen_q, ", Зал Quality =", state.hall_q)
    print("Выберите, что улучшить:")
    print("  1. Кухня")
    print("  2. Зал")
    choice = input("Ваш выбор (1/2/отмена): ").strip()
    if choice not in ('1','2'):
        return
    slot = 'кухни' if choice == '1' else 'зала'
    print("Доступные уровни:")
    for k, (name, price, q) in tiers.items():
        print(f"  {k}. {name}: ${price} (Quality +{q})")
    tier_choice = input("Выберите уровень (1-3): ").strip()
    if tier_choice not in tiers:
        return
    name, price, q = tiers[tier_choice]
    if state.budget < price:
        print("Недостаточно средств!")
        return
    if choice == '1':
        state.kitchen_q = q
    else:
        state.hall_q = q
    state.budget -= price
    print(f"Оборудование {slot} обновлено до '{name}' Quality={q}. Потрачено ${price}.")

def main():
    print("🌟 Добро пожаловать в ресторанный симулятор! 🌟")
    state = GameState()

    # === Initialisation ===
    print(f"\nНачальный бюджет: ${state.budget:.2f}")
    # Buy equipment
    (k_q, k_price), (h_q, h_price) = choose_equipment()
    total_equip_cost = k_price + h_price
    if state.budget < total_equip_cost:
        print("У вас не хватает денег даже на самое дешёвое оборудование! Игра окончена.")
        return
    state.budget -= total_equip_cost
    state.kitchen_q = k_q
    state.hall_q = h_q
    print(f"Оборудование куплено. Бюджет: ${state.budget:.2f}")

    # Hire initial staff
    hire_menu(state)

    if not state.staff_list:
        print("Вы не наняли ни одного сотрудника. Ресторан не может работать.")
        return

    # === Main game loop ===
    while True:
        # Display status before actions
        print(f"\nТик {state.tick} | Бюджет: ${state.budget:.2f} | Репутация: {state.reputation} | Персонал: {len(state.staff_list)} | Очередь: {len(state.guest_queue)}")
        cmd = input("Действие: next / hire / fire / shop / status / quit: ").strip().lower()

        if cmd == 'next':
            events = process_tick(state)
            for e in events:
                print(e)
            if state.reputation < 0:
                print("Игра окончена. Вы обанкротились!")
                break
            if state.budget < -500:   # optional extra loose condition
                print("У вас огромные долги. Игра завершена.")
                break

        elif cmd == 'hire':
            hire_menu(state)

        elif cmd == 'fire':
            if not state.staff_list:
                print("Нет персонала для увольнения.")
                continue
            for i, s in enumerate(state.staff_list):
                status = "свободен" if s.is_free else "занят/отдых"
                print(f"  {i+1}. Навык={s.skill}, Стамина={s.stamina}, Зарплата=${s.salary}, Статус={status}")
            try:
                idx = int(input("Номер для увольнения (0 – отмена): ")) - 1
                if idx >= 0:
                    state.fire_staff(idx)
                    print("Сотрудник уволен.")
            except:
                pass

        elif cmd == 'shop':
            shop_menu(state)

        elif cmd == 'status':
            print("\n=== Состояние ресторана ===")
            print(f"Бюджет: ${state.budget:.2f}  Репутация: {state.reputation}")
            print(f"Оборудование: Кухня Q={state.kitchen_q}, Зал Q={state.hall_q} (среднее={state.equipment_quality:.1f})")
            print("Персонал:")
            for i, s in enumerate(state.staff_list):
                free = "✅ Свободен" if s.is_free else "⛔ Занят/выдохся"
                print(f"  {i+1}. Навык={s.skill}, Стамина={s.stamina}/{s.max_stamina}, Зарплата=${s.salary}, {free}")
            print(f"Гостей в очереди: {len(state.guest_queue)}")
            for g in state.guest_queue:
                print(f"  - Бюджет=${g.budget:.1f}, Терпение={g.patience}, Ожидают={g.wait_timer} тиков, Ожидания={g.expectation:.1f}")

        elif cmd == 'quit':
            print("До свидания!")
            break
        else:
            print("Неизвестная команда.")

if __name__ == "__main__":
    main()