from browser_controller import BrowserController
from agent import AutonomousAgent

def main():
    print("Надо сюда ввести задачу (например: 'Закажи бургер из яндекс еды на мой адрес').\n")

    task = input("Опиши задачу для агента: ").strip()
    if not task:
        print("Пустая задача. Закрытие")
        return

    browser = BrowserController(user_data_dir="user_data")
    agent = AutonomousAgent(browser)

    try:
        agent.run(task)
        input(
            "\nАгент закончил. Теперь ты можешь вручную ввести данные карты "
            "и завершить заказ в открытом браузере.\n"
            "Когда всё сделаешь и хочешь закрыть браузер - нажми Enter!!!!!!!!!"
        )
    finally:
        browser.close()

if __name__ == "__main__":
    main()
