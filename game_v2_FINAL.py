import random
from typing import List

# ---------------------- Helper classes ----------------------
class Staff:
    def __init__(self, skill: int, salary_per_minute: int):
        self.skill = skill
        self.max_stamina = 100
        self.stamina = self.max_stamina
        self.salary_per_minute = salary_per_minute  # base pay for 1 real minute
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
            self.forced_rest = True

    def tick_update(self):
        """Called every tick to advance internal timers."""
        if self.forced_rest:
            return
        if self.busy_timer > 0:
            self.busy_timer -= 1
        if self.stamina == 0:
            self.forced_rest = True
            self.busy_timer = 0

class Guest:
    def __init__(self, budget: float, patience_ticks: int, expectation: float, mood: int):
        self.budget = budget
        self.patience_ticks = patience_ticks  # how many ticks they are willing to wait
        self.expectation = expectation
        self.mood = mood
        self.wait_timer = 0

class GameState:
    def __init__(self):
        self.budget = 200.0
        self.reputation = 0.0
        self.kitchen_q = 0
        self.hall_q = 0
        self.staff_list: List[Staff] = []
        self.guest_queue: List[Guest] = []
        self.tick = 0
        # Day settings
        self.tick_minutes = 5          # default 5 minutes per tick, will be set by player
        self.total_ticks = 144         # 12 hours / 5 min = 144 ticks
        self.start_minute = 9 * 60     # 09:00 in minutes
        # Statistics
        self.served_total = 0
        self.served_success = 0
        self.served_fail = 0
        self.left_guests = 0

    @property
    def equipment_quality(self) -> float:
        return (self.kitchen_q + self.hall_q) / 2.0

    def hire_staff(self, skill: int, salary_per_minute: int):
        self.staff_list.append(Staff(skill, salary_per_minute))

    def fire_staff(self, index: int):
        if 0 <= index < len(self.staff_list):
            self.staff_list.pop(index)

    def current_time_str(self) -> str:
        """Return current in-game time as HH:MM."""
        minutes = self.start_minute + self.tick * self.tick_minutes
        h = (minutes // 60) % 24
        m = minutes % 60
        return f"{h:02d}:{m:02d}"

    def time_remaining(self) -> int:
        """Return remaining ticks until day ends."""
        return max(0, self.total_ticks - self.tick)

# ---------------------- Game logic ----------------------
def spawn_guest(state: GameState):
    """Attempt to spawn a new guest based on current reputation."""
    base_rate = 0.3
    mult = 1 + state.reputation * 0.01
    if mult < 0.1:
        mult = 0.1
    spawn_chance = base_rate * mult * random.uniform(0.8, 1.2)
    if random.random() < spawn_chance:
        budget = max(5.0, random.gauss(40, 15))
        # Base patience in real minutes (5..15), convert to ticks
        base_patience_min = random.randint(5, 15)
        patience_ticks = max(1, base_patience_min // state.tick_minutes)
        base_exp = 3.0
        expectation = base_exp + state.reputation * 0.05
        mood = random.randint(1, 10)
        state.guest_queue.append(Guest(budget, patience_ticks, expectation, mood))
        return True
    return False

def process_tick(state: GameState) -> List[str]:
    """Execute one full tick, return a list of event messages."""
    events = []
    state.tick += 1
    events.append(f"--- Тик {state.tick} ({state.current_time_str()}) ---")

    # Day ended?
    if state.tick > state.total_ticks:
        events.append("🏁 Рабочий день завершён!")
        return events

    # 1. Check bankruptcy
    if state.reputation < 0:
        events.append("💥 Ваша репутация опустилась ниже нуля! Банкротство.")
        return events

    # 2. Update staff
    for i, staff in enumerate(state.staff_list):
        staff.tick_update()
        if staff.forced_rest:
            events.append(f"⚙️ Персонал #{i+1} выдохся и больше не может работать.")

    # 3. Spawn new guest (only during working hours)
    if spawn_guest(state):
        events.append("🎲 Появился новый гость!")

    # 4. Assign free staff to waiting guests
    free_staff = [s for s in state.staff_list if s.is_free]
    while free_staff and state.guest_queue:
        staff = free_staff.pop(0)
        guest = state.guest_queue.pop(0)

        quality = staff.skill * 0.7 + state.equipment_quality * 0.3
        staff.start_service(base_stamina_drain=10)
        state.served_total += 1

        if quality >= guest.expectation:
            income = guest.budget * 1.2
            state.budget += income
            state.reputation += 3
            state.served_success += 1
            events.append(f"😊 Успешное обслуживание! +${income:.2f}, репутация +3.")
        else:
            loss = guest.budget
            state.budget -= loss
            state.reputation -= 10
            state.served_fail += 1
            events.append(f"😞 Провал! -${loss:.2f}, репутация -10.")

    # 5. Handle waiting guests
    for guest in list(state.guest_queue):
        guest.wait_timer += 1
        if guest.wait_timer >= guest.patience_ticks:
            state.guest_queue.remove(guest)
            state.reputation -= 5
            state.left_guests += 1
            events.append(f"😤 Гость ушёл из-за долгого ожидания. Репутация -5.")

    # 6. Pay salaries (scale by tick length)
    total_salary = sum(s.salary_per_minute * state.tick_minutes for s in state.staff_list)
    state.budget -= total_salary
    events.append(f"💼 Зарплаты: -${total_salary:.2f}.")

    events.append(f"💰 Бюджет: ${state.budget:.2f} | ⭐ Репутация: {state.reputation} | 👥 Очередь: {len(state.guest_queue)}")
    return events

def run_ticks(state: GameState, n: int) -> List[str]:
    """Run N ticks silently, return only the last status line or special events."""
    final_events = []
    for _ in range(n):
        if state.tick >= state.total_ticks or state.reputation < 0:
            break
        ev = process_tick(state)
        final_events = ev  # keep last tick's events
    return final_events

# ---------------------- User interface ----------------------
def choose_equipment():
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
    print("\n👥 Найм персонала.")
    while True:
        skill = random.randint(1, 10)
        salary_per_min = skill * 5   # $5 per skill per minute
        effective_per_tick = salary_per_min * state.tick_minutes
        print(f"Кандидат: Навык={skill}, Зарплата=${salary_per_min}/мин (${effective_per_tick}/тик).")
        ans = input("Нанять? (y/n/stop): ").strip().lower()
        if ans == 'y':
            if state.budget < effective_per_tick:
                print("Недостаточно бюджета для зарплаты этого сотрудника!")
            else:
                state.hire_staff(skill, salary_per_min)
                print(f"Сотрудник нанят! Персонал: {len(state.staff_list)} чел.")
        elif ans == 'stop':
            break
        else:
            continue
        if input("Нанять ещё? (y/n): ").strip().lower() != 'y':
            break

def shop_menu(state: GameState):
    tiers = {
        '1': ('🟢 Дешёвое', 30, 1),
        '2': ('🟡 Нормальное', 60, 3),
        '3': ('🔴 Дорогое', 100, 5)
    }
    print("\n🛒 Обновление оборудования.")
    print(f"Текущее: Кухня Quality={state.kitchen_q}, Зал Quality={state.hall_q}")
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

def show_day_summary(state: GameState):
    print("\n" + "="*40)
    print("         📊 ИТОГИ ДНЯ")
    print("="*40)
    print(f"🕒 Время закрытия: {state.current_time_str()}")
    print(f"💰 Начальный бюджет: $200.00")
    print(f"💰 Конечный бюджет: ${state.budget:.2f}")
    profit = state.budget - 200.0
    print(f"📈 Чистая прибыль: ${profit:.2f}")
    print(f"⭐ Репутация: {state.reputation}")
    print(f"👥 Обслужено гостей: {state.served_total}")
    print(f"   ✅ Успешно: {state.served_success}")
    print(f"   ❌ Неудачно: {state.served_fail}")
    print(f"🚶 Ушло без обслуживания: {state.left_guests}")
    print(f"👨‍🍳 Персонал на конец дня: {len(state.staff_list)}")
    if state.reputation < 0:
        print("💥 РЕСТОРАН ОБАНКРОТИЛСЯ!")
    print("="*40)

def main():
    print("🌟 Добро пожаловать в ресторанный симулятор! 🌟")
    state = GameState()

    # ---- Time scale ----
    print("\n⏱️ Выберите длительность одного тика (игровых минут):")
    options = {'1': 1, '5': 5, '10': 10, '15': 15, '30': 30}
    while True:
        sel = input("1 / 5 / 10 / 15 / 30 (по умолчанию 5): ").strip()
        if sel == '':
            sel = '5'
        if sel in options:
            state.tick_minutes = options[sel]
            break
        print("Пожалуйста, введите одно из чисел.")
    day_duration = 12 * 60  # 12 hours in minutes
    state.total_ticks = day_duration // state.tick_minutes
    print(f"Рабочий день продлится {state.total_ticks} тиков (с 09:00 до 21:00).")

    # ---- Initial budget & equipment ----
    print(f"\nНачальный бюджет: ${state.budget:.2f}")
    (k_q, k_price), (h_q, h_price) = choose_equipment()
    total_cost = k_price + h_price
    if state.budget < total_cost:
        print("У вас не хватает денег даже на самое дешёвое оборудование! Игра окончена.")
        return
    state.budget -= total_cost
    state.kitchen_q = k_q
    state.hall_q = h_q
    print(f"Оборудование куплено. Бюджет: ${state.budget:.2f}")

    # ---- Hire initial staff ----
    hire_menu(state)
    if not state.staff_list:
        print("Вы не наняли ни одного сотрудника. Ресторан не может работать.")
        return

    # ---- Main loop ----
    while True:
        if state.tick >= state.total_ticks or state.reputation < 0:
            break
        print(f"\n[{state.current_time_str()}] Тик {state.tick+1}/{state.total_ticks} | 💰${state.budget:.2f} | ⭐{state.reputation} | 👥{len(state.staff_list)} | Очередь:{len(state.guest_queue)}")
        cmd = input("Действие: next / run N / hire / fire / shop / status / quit: ").strip().lower()

        if cmd == 'next':
            events = process_tick(state)
            for e in events:
                print(e)
            if state.reputation < 0:
                print("Вы обанкротились!")
                break

        elif cmd.startswith('run'):
            parts = cmd.split()
            if len(parts) == 2 and parts[1].isdigit():
                n = int(parts[1])
                n = min(n, state.time_remaining())
                if n > 0:
                    print(f"⏩ Пропускаем {n} тиков...")
                    events = run_ticks(state, n)
                    for e in events:
                        print(e)
                if state.reputation < 0:
                    print("Банкротство во время ускоренного прогона.")
                    break
            else:
                print("Использование: run <число>")

        elif cmd == 'hire':
            hire_menu(state)

        elif cmd == 'fire':
            if not state.staff_list:
                print("Нет персонала для увольнения.")
                continue
            for i, s in enumerate(state.staff_list):
                eff_salary = s.salary_per_minute * state.tick_minutes
                status = "свободен" if s.is_free else "занят/отдых"
                print(f"  {i+1}. Навык={s.skill}, Стамина={s.stamina}, Зарплата=${eff_salary}/тик, Статус={status}")
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
            print(f"Время: {state.current_time_str()} (осталось тиков: {state.time_remaining()})")
            print(f"Бюджет: ${state.budget:.2f}  Репутация: {state.reputation}")
            print(f"Оборудование: Кухня Q={state.kitchen_q}, Зал Q={state.hall_q} (среднее={state.equipment_quality:.1f})")
            print("Персонал:")
            for i, s in enumerate(state.staff_list):
                free = "✅ Свободен" if s.is_free else "⛔ Занят/выдохся"
                print(f"  {i+1}. Навык={s.skill}, Стамина={s.stamina}/{s.max_stamina}, Зарплата=${s.salary_per_minute * state.tick_minutes}/тик, {free}")
            print(f"Гостей в очереди: {len(state.guest_queue)}")
            for g in state.guest_queue:
                print(f"  - Бюджет=${g.budget:.1f}, Терпение={g.patience_ticks} тиков, Ожидают={g.wait_timer}, Ожидания={g.expectation:.1f}")
            print(f"Статистика: обслужено {state.served_total} (успех {state.served_success}, провал {state.served_fail}), ушло {state.left_guests}")

        elif cmd == 'quit':
            print("Досрочное завершение дня.")
            break
        else:
            print("Неизвестная команда.")

    # ---- End of day ----
    show_day_summary(state)
    print("Спасибо за игру!")

if __name__ == "__main__":
    main()