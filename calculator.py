from typing import List, Tuple, Dict, Any
from collections import defaultdict


class DebtCalculator:
    @staticmethod
    def calculate_debts(expenses: List[Tuple]) -> Tuple[Dict[str, float], List[Tuple]]:
        """
        Расчет долгов на основе расходов

        Returns:
            Tuple с балансами пользователей (по именам) и списком долгов
        """
        total_spent = 0.0
        user_spends = defaultdict(float)

        for expense in expenses:
            user_name = expense[2]  # full_name
            amount = expense[3]

            total_spent += amount
            user_spends[user_name] += amount

        if total_spent == 0:
            return {}, []

        share = total_spent / 3
        balances = {}
        for user_name, spent in user_spends.items():
            balances[user_name] = spent - share

        creditors = []
        debtors = []

        for user_name, balance in balances.items():
            if balance > 0.01:
                creditors.append((user_name, balance))
            elif balance < -0.01:
                debtors.append((user_name, abs(balance)))

        creditors.sort(key=lambda x: x[1], reverse=True)
        debtors.sort(key=lambda x: x[1], reverse=True)

        debts_list = []
        creditor_index = 0
        debtor_index = 0

        while creditor_index < len(creditors) and debtor_index < len(debtors):
            creditor_name, credit_amount = creditors[creditor_index]
            debtor_name, debt_amount = debtors[debtor_index]

            transfer = min(credit_amount, debt_amount)

            debts_list.append((
                debtor_name, creditor_name, transfer
            ))

            credit_amount -= transfer
            debt_amount -= transfer

            creditors[creditor_index] = (creditor_name, credit_amount)
            debtors[debtor_index] = (debtor_name, debt_amount)

            if credit_amount < 0.01:
                creditor_index += 1
            if debt_amount < 0.01:
                debtor_index += 1

        return balances, debts_list

    @staticmethod
    def format_debts_message(balances: Dict[str, float], debts: List[Tuple], total_spent: float) -> str:
        """Форматирование сообщения с долгами"""
        if not balances:
            return "📊 Пока нет никаких расходов"

        share = total_spent / 3
        message = [
            "💸 *Текущие расчеты:*",
            f"Общая сумма: {total_spent:.2f} руб.",
            f"Доля каждого: {share:.2f} руб.",
            "",
            "📋 *Балансы:*"
        ]

        for user_name, balance in balances.items():
            status = "✅" if abs(balance) < 0.01 else "➖" if balance < 0 else "➕"
            message.append(f"{status} {user_name}: {balance:+.2f} руб.")

        if debts:
            message.extend(["", "🤝 *Кто кому должен:*"])
            for i, (debtor_name, creditor_name, amount) in enumerate(debts, 1):
                message.append(f"{i}. {debtor_name} → {creditor_name}: {amount:.2f} руб.")

        return "\n".join(message)