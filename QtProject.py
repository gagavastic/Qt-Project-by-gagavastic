import sys
import io
import datetime as dt
import csv
import os
import math
import sqlite3  
from tkinter import ttk
from PyQt6 import QtWidgets, uic
from PyQt6 import QtCore
from PyQt6 import QtGui
from PyQt6.QtCore import QDateTime, QTimer, Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QListWidgetItem, QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QListWidget, QComboBox
from PyQt6.QtGui import QTextCursor, QTextCharFormat


class DatabaseManager:
    def __init__(self, db_path='budget_data.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS budget_maps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                total_budget REAL NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                initial_balance REAL NOT NULL,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS budget_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                budget_map_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                item_amount REAL NOT NULL,
                FOREIGN KEY (budget_map_id) REFERENCES budget_maps (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_spendings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                item_name TEXT NOT NULL,
                amount REAL NOT NULL,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def clear_all_data(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM budget_maps')
        cursor.execute('DELETE FROM budget_items')
        cursor.execute('DELETE FROM daily_spendings')
        conn.commit()
        conn.close()
        print("Все данные очищены из БД")
    
    def save_budget_map(self, budget_data):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO budget_maps (total_budget, start_date, end_date, initial_balance)
            VALUES (?, ?, ?, ?)
        ''', (
            budget_data['total_budget'],
            budget_data['start_date'].strftime('%Y-%m-%d'),
            budget_data['end_date'].strftime('%Y-%m-%d'),
            budget_data['initial_ostatok']
        ))
        
        budget_map_id = cursor.lastrowid
        
        for item_name, item_amount in budget_data['items']:
            cursor.execute('''
                INSERT INTO budget_items (budget_map_id, item_name, item_amount)
                VALUES (?, ?, ?)
            ''', (budget_map_id, item_name, item_amount))
        
        conn.commit()
        conn.close()
        return budget_map_id
    
    def get_latest_budget_map(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, total_budget, start_date, end_date, initial_balance 
            FROM budget_maps 
            ORDER BY created_date DESC LIMIT 1
        ''')
        
        budget_row = cursor.fetchone()
        if not budget_row:
            conn.close()
            return None
        
        budget_id, total_budget, start_date, end_date, initial_balance = budget_row
        
        cursor.execute('''
            SELECT item_name, item_amount 
            FROM budget_items 
            WHERE budget_map_id = ?
        ''', (budget_id,))
        
        items = cursor.fetchall()
        conn.close()
        
        return {
            'items': items,
            'total_budget': total_budget,
            'start_date': dt.datetime.strptime(start_date, '%Y-%m-%d').date(),
            'end_date': dt.datetime.strptime(end_date, '%Y-%m-%d').date(),
            'initial_ostatok': initial_balance,
            'actual_ostatok': total_budget
        }
    
    def save_daily_spendings(self, date, spendings):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        date_str = date.strftime('%Y-%m-%d')
        
        cursor.execute('DELETE FROM daily_spendings WHERE date = ?', (date_str,))
        
        for spending in spendings:
            cursor.execute('''
                INSERT INTO daily_spendings (date, item_name, amount)
                VALUES (?, ?, ?)
            ''', (date_str, spending['item_name'], spending['summa']))
        
        conn.commit()
        conn.close()
        print(f"Сохранено {len(spendings)} трат за {date_str}")
    
    def get_all_daily_spendings(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT date, item_name, amount 
            FROM daily_spendings 
            ORDER BY date
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        daily_spendings = {}
        for date_str, item_name, amount in rows:
            if date_str not in daily_spendings:
                daily_spendings[date_str] = []
            
            daily_spendings[date_str].append({
                'item_name': item_name,
                'summa': amount,
                'display_text': f"{item_name} (бюджет: ... руб.)"
            })
        
        return daily_spendings
    
    def get_spendings_by_date_range(self, start_date, end_date):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT date, item_name, amount 
            FROM daily_spendings 
            WHERE date BETWEEN ? AND ?
            ORDER BY date
        ''', (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
        
        rows = cursor.fetchall()
        conn.close()
        
        return rows


class StatisticsDialog(QDialog):
    def __init__(self, parent=None, budget_map_data=None, daily_spendings_data=None):
        super().__init__(parent)
        self.parent = parent
        self.budget_map_data = budget_map_data
        self.daily_spendings_data = daily_spendings_data
        
        self.setWindowTitle("Статистика бюджета")
        self.setGeometry(350, 350, 700, 600)
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        title_label = QLabel("СТАТИСТИКА БЮДЖЕТА")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold; margin: 10px; color: #2c3e50;")
        layout.addWidget(title_label)
        
        self.stats_list = QListWidget()
        layout.addWidget(self.stats_list)
                
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        self.populate_statistics()

        self.setLayout(layout)
    
    def calculate_total_spent_by_item(self):
        spents = {}
        if not self.budget_map_data or 'items' not in self.budget_map_data:
            return spents
            
        for item_name, _ in self.budget_map_data['items']:
            spents[item_name] = 0.0
        
        if self.daily_spendings_data:
            for date_str, spendings in self.daily_spendings_data.items():
                for spending in spendings:
                    item_name = spending['item_name']
                    summa = spending['summa']
                    if item_name in spents:
                        spents[item_name] += summa
        
        return spents
    
    def calculate_day_stats(self):
        day_totals = {}
        weekday_totals = {i: [] for i in range(7)}
        
        if self.daily_spendings_data:
            for date_str, spendings in self.daily_spendings_data.items():
                try:
                    date = dt.datetime.strptime(date_str, '%Y-%m-%d').date()
                    total_day = sum(spending['summa'] for spending in spendings)
                    day_totals[date_str] = total_day
                    weekday_totals[date.weekday()].append(total_day)
                except ValueError:
                    continue
        
        max_day = (None, 0.0)
        if day_totals:
            max_day = max(day_totals.items(), key=lambda x: x[1])
            weekday_sredne = {}
        for weekday, summi in weekday_totals.items():
            if summi:
                weekday_sredne[weekday] = sum(summi) / len(summi)
        
        max_weekday = (0, 0.0)

        if weekday_sredne:
            max_weekday = max(weekday_sredne.items(), key=lambda x: x[1])
        
        weekday_names = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
        weekday_name = weekday_names[max_weekday[0]]
        
        return max_day, weekday_name
    
    def calculate_max_exceed(self, item_spent):
        max_bigger_item = None
        max_bigger_summa = 0.0
        
        for item_name, spent in item_spent.items():
            item_budget = 0.0
            for budget_item, budget_summa in self.budget_map_data['items']:
                if budget_item == item_name:
                    item_budget = budget_summa
                    break
            
            if spent > item_budget:
                exceed = spent - item_budget
                if exceed > max_bigger_summa:
                    max_bigger_summa = exceed
                    max_bigger_item = item_name
        
        return max_bigger_item, max_bigger_summa
    
    def calculate_budget_adherence(self, total_spent):
        total_budget = self.budget_map_data['total_budget']
        if total_budget == 0:
            return 0.0
        
        otklonenie = total_spent - total_budget
        proccent = (otklonenie / total_budget) * 100
        if otklonenie > 0:
            proccent = math.ceil(proccent * 10) / 10
        else:
            proccent = math.floor(proccent * 10) / 10
        
        return proccent
    
    def get_advice(self, item_spent, total_spent, budget_adherence):
        total_budget = self.budget_map_data['total_budget']
        
        exceeded_items = []
        for item_name, spent in item_spent.items():
            item_budget = 0.0
            for budget_item, budget_summa in self.budget_map_data['items']:
                if budget_item == item_name:
                    item_budget = budget_summa
                    break
            if spent > item_budget:
                exceeded_items.append(item_name)
        
        if total_spent == 0:
            return "Да вы, батюшка, аскет!", QtGui.QColor(100, 200, 100)
        
        if budget_adherence > 500:
            return "0_0", QtGui.QColor(255, 100, 100)
        
        all_items_count = len(self.budget_map_data['items'])
        
        if total_spent <= total_budget and not exceeded_items:
            return "Вы огромный молодец и справились с поставленной задачей. Так держать!", QtGui.QColor(100, 200, 100)
        elif total_spent <= total_budget and exceeded_items:
            items_str = ", ".join(exceeded_items)
            return f"Неплохо, но вам следует поработать над вашим распределением доходов по следующим пунктам: {items_str}.", QtGui.QColor(255, 200, 100)
        elif total_spent > total_budget and exceeded_items:
            items_str = ", ".join(exceeded_items)
            return f"Вам следует поработать над вашим распределением доходов по следующим пунктам: {items_str}.", QtGui.QColor(255, 150, 100)
        elif len(exceeded_items) == all_items_count:
            return "Просто ужасная работа с распределением доходов! Вам следует лучше следить куда вы тратите заработанное!", QtGui.QColor(255, 100, 100)
        else:
            return "Проанализируйте ваши траты и попробуйте оптимизировать бюджет.", QtGui.QColor(200, 200, 200)
    
    def populate_statistics(self):
        self.stats_list.clear()
    
        title_item = QListWidgetItem("=== КАРТА БЮДЖЕТА ===")
        title_item.setBackground(QtGui.QColor(230, 240, 255))
        self.stats_list.addItem(title_item)
    
        total_budget = self.budget_map_data['total_budget']
        budget_item = QListWidgetItem(f"Общий бюджет: {total_budget:.1f} руб.")
        budget_item.setBackground(QtGui.QColor(240, 245, 255))
        self.stats_list.addItem(budget_item)
    
        for item_name, item_summa in self.budget_map_data['items']:
            item_text = f"  {item_name} - {item_summa:.1f} руб."
            item_list_item = QListWidgetItem(item_text)
            item_list_item.setBackground(QtGui.QColor(240, 245, 255))
            self.stats_list.addItem(item_list_item)
    
        self.stats_list.addItem(QListWidgetItem("")) 
    
        total_spent = sum(
            sum(spending['summa'] for spending in spendings)
            for spendings in self.daily_spendings_data.values()
        ) if self.daily_spendings_data else 0.0
    
        total_item = QListWidgetItem(f"ИТОГОВАЯ СУММА ПОТРАЧЕННОГО: {total_spent:.1f} руб.")
        total_item.setBackground(QtGui.QColor(200, 230, 255))
        self.stats_list.addItem(total_item)
    
        self.stats_list.addItem(QListWidgetItem(""))
    
        self.stats_list.addItem(QListWidgetItem("ТРАТЫ ПО ПУНКТАМ:"))
    
        item_spent = self.calculate_total_spent_by_item()
        for item_name, spent in item_spent.items():
            item_budget = 0.0
            for budget_item, budget_summa in self.budget_map_data['items']:
                if budget_item == item_name:
                    item_budget = budget_summa
                    break
        
            if item_budget > 0:
                proccennt = (spent / item_budget) * 100
                proccennt = round(proccennt, 1)
            else:
                proccennt = 0.0
        
            item_text = f"  {item_name} – {spent:.1f} руб. ({proccennt:.1f}%)"
            item_list_item = QListWidgetItem(item_text)
        
            if spent <= item_budget:
                item_list_item.setBackground(QtGui.QColor(200, 255, 200))
            else:
                item_list_item.setBackground(QtGui.QColor(255, 200, 200))
        
            self.stats_list.addItem(item_list_item)
    
        self.stats_list.addItem(QListWidgetItem("")) 
    
        max_day, max_weekday = self.calculate_day_stats()

        if max_day[0]:
            max_day_date = dt.datetime.strptime(max_day[0], '%Y-%m-%d').strftime('%d.%m.%Y')
            max_day_item = QListWidgetItem(f"ДЕНЬ МАКСИМАЛЬНЫХ ТРАТ: {max_day_date} - {max_day[1]:.1f} руб.")
        
            total_budget = self.budget_map_data['total_budget']
            if max_day[1] > total_budget:
                max_day_item.setBackground(QtGui.QColor(255, 150, 150))
            else:
                max_day_item.setBackground(QtGui.QColor(255, 220, 220))
        
            self.stats_list.addItem(max_day_item)
        else:
            self.stats_list.addItem(QListWidgetItem("ДЕНЬ МАКСИМАЛЬНЫХ ТРАТ: Нет данных"))
    
        self.stats_list.addItem(QListWidgetItem(f"ДЕНЬ НЕДЕЛИ С МАКС. ТРАТАМИ: {max_weekday}"))
    
        self.stats_list.addItem(QListWidgetItem(""))  

        max_exceed_item, max_exceed_summa = self.calculate_max_exceed(item_spent)
        if max_exceed_item:
            exceed_item = QListWidgetItem(f"МАКСИМАЛЬНОЕ ПРЕВЫШЕНИЕ: {max_exceed_item} - {max_exceed_summa:.1f} руб.")
            exceed_item.setBackground(QtGui.QColor(255, 200, 200))
            self.stats_list.addItem(exceed_item)
        else:
            exceed_item = QListWidgetItem("МАКСИМАЛЬНОЕ ПРЕВЫШЕНИЕ: Отсутствуют 😊")
            exceed_item.setBackground(QtGui.QColor(200, 255, 200))
            self.stats_list.addItem(exceed_item)
    
        self.stats_list.addItem(QListWidgetItem(""))  
    
        budget_deafult = self.calculate_budget_adherence(total_spent)
    
        otklonnenie_ot_summo = total_spent - total_budget
    
        adherence_proccent = abs(budget_deafult)
    
        if otklonnenie_ot_summo >= 0:
            deviation_text = f"ПРЕВЫШЕНИЕ БЮДЖЕТА: {otklonnenie_ot_summo:.1f} руб. ({adherence_proccent:.1f}%)"
        else:
            deviation_text = f"ЭКОНОМИЯ БЮДЖЕТА: {abs(otklonnenie_ot_summo):.1f} руб. ({adherence_proccent:.1f}%)"
    
        adherence_item = QListWidgetItem(deviation_text)
    
        if otklonnenie_ot_summo <= 0:
            adherence_item.setBackground(QtGui.QColor(200, 255, 200))
        else:
            adherence_item.setBackground(QtGui.QColor(255, 200, 200))
    
        self.stats_list.addItem(adherence_item)
    
        self.stats_list.addItem(QListWidgetItem(""))  
        self.stats_list.addItem(QListWidgetItem("─" * 50))
        self.stats_list.addItem(QListWidgetItem(""))  
    
        advice, advice_color = self.get_advice(item_spent, total_spent, budget_deafult)
        advice_item = QListWidgetItem("СОВЕТ:")
        advice_item.setBackground(QtGui.QColor(250, 250, 200))
        self.stats_list.addItem(advice_item)
    
        advice_text_item = QListWidgetItem(advice)
        advice_text_item.setBackground(advice_color)
        self.stats_list.addItem(advice_text_item)


class DaySpendingsViewDialog(QDialog):
    def __init__(self, parent=None, selected_date=None, budget_map_data=None, daily_spendings_data=None):
        super().__init__(parent)
        self.parent = parent
        self.selected_date = selected_date
        self.budget_map_data = budget_map_data
        self.daily_spendings_data = daily_spendings_data
        
        self.setWindowTitle("Просмотр трат за день")
        self.setGeometry(350, 350, 600, 500)
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        date_label = QLabel(f"Траты за {self.selected_date.strftime('%d.%m.%Y')}")
        date_label.setStyleSheet("font-size: 14pt; font-weight: bold; margin: 10px;")
        layout.addWidget(date_label)
        
        self.spendings_list = QListWidget()
        layout.addWidget(self.spendings_list)
        
        self.populate_spendings_list()
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
    
    def calculate_ostatok_for_items(self):
        ostatok_budget = {}
        for item_name, item_summa in self.budget_map_data['items']:
            ostatok_budget[item_name] = item_summa
        
        for date_str, spendings in self.daily_spendings_data.items():
            spending_date = dt.datetime.strptime(date_str, '%Y-%m-%d').date()
            if spending_date < self.selected_date:
                for spending in spendings:
                    item_name = spending['item_name']
                    if item_name in ostatok_budget:
                        ostatok_budget[item_name] -= spending['summa']
        
        return ostatok_budget
    
    def populate_spendings_list(self):
        date_str = self.selected_date.strftime('%Y-%m-%d')
        
        ostatok_budget_start = self.calculate_ostatok_for_items()
        
        if date_str in self.daily_spendings_data:
            spendings = self.daily_spendings_data[date_str]
            total_day_spent = 0
            
            ostatok = ostatok_budget_start.copy()
            
            for spending in spendings:
                item_name = spending['item_name']
                summa = spending['summa']
                total_day_spent += summa
                
                ostatok_before_spending = ostatok.get(item_name, 0)
                
                if item_name in ostatok:
                    ostatok[item_name] -= summa
                
                item_total_budget = 0
                for budget_item, budget_summa in self.budget_map_data['items']:
                    if budget_item == item_name:
                        item_total_budget = budget_summa
                        break
                
                if ostatok_before_spending > 0:
                    if summa > ostatok_before_spending + 0.01:
                        color = QtGui.QColor(255, 200, 200)
                        status = "ПРЕВЫШЕНИЕ ОСТАТКА"
                    elif summa >= ostatok_before_spending * 0.85: 
                        color = QtGui.QColor(255, 255, 200)
                        status = "БОЛЬШАЯ ЧАСТЬ ОСТАТКА"
                    else:
                        color = QtGui.QColor(200, 255, 200)
                        status = "НОРМА"
                    
                    item_text = f"{item_name} - {summa:.2f} руб. (остаток было: {ostatok_before_spending:.2f} руб.) - {status}"
                elif ostatok_before_spending == 0:
                    color = QtGui.QColor(255, 150, 150)
                    status = "НЕТ ОСТАТКА"
                    item_text = f"{item_name} - {summa:.2f} руб. (остаток было: 0.00 руб.) - {status}"
                else:
                    color = QtGui.QColor(255, 100, 100)
                    status = "УЖЕ ПРЕВЫШЕНО"
                    item_text = f"{item_name} - {summa:.2f} руб. (остаток было: {ostatok_before_spending:.2f} руб.) - {status}"
                
                list_item = QListWidgetItem(item_text)
                list_item.setBackground(color)
                self.spendings_list.addItem(list_item)
            
            self.spendings_list.addItem(QListWidgetItem("─" * 60))
            
            self.spendings_list.addItem(QListWidgetItem("Остатки после трат:"))
            for item_name in ostatok:
                ostatok_start = ostatok_budget_start.get(item_name, 0)
                ostatok_end = ostatok.get(item_name, 0)
                
                if date_str in self.daily_spendings_data:
                    day_spendings_for_item = [s for s in self.daily_spendings_data[date_str] if s['item_name'] == item_name]
                    if day_spendings_for_item:
                        ostatok_item = QListWidgetItem(f"  {item_name}: {ostatok_end:.2f} руб.")
                        if ostatok_end < 0:
                            ostatok_item.setForeground(QtGui.QColor(255, 0, 0))
                        elif ostatok_end < ostatok_start * 0.15:
                            ostatok_item.setForeground(QtGui.QColor(255, 165, 0))
                        self.spendings_list.addItem(ostatok_item)
            
            total_item = QListWidgetItem(f"ВСЕГО ЗА ДЕНЬ: {total_day_spent:.2f} руб.")
            total_item.setBackground(QtGui.QColor(180, 200, 255))
            self.spendings_list.addItem(total_item)
            
        else:
            no_data_item = QListWidgetItem("Трат за этот день не зафиксировано")
            no_data_item.setBackground(QtGui.QColor(240, 240, 240))
            self.spendings_list.addItem(no_data_item)


class DaySpendingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Учет дневных трат")
        self.setGeometry(300, 300, 700, 500)
        
        self.daily_spendings = []
        self.selected_date = dt.date.today()
        
        self.load_existing_spendings()
        
        self.init_ui()
        
    def load_existing_spendings(self):
        if self.parent and hasattr(self.parent, 'daily_spendings_data'):
            today_str = self.selected_date.strftime('%Y-%m-%d')
            if today_str in self.parent.daily_spendings_data:
                self.daily_spendings = self.parent.daily_spendings_data[today_str].copy()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        date_label = QLabel(f"Траты за {self.selected_date.strftime('%d.%m.%Y')}")
        date_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(date_label)
        
        input_layout = QHBoxLayout()
        
        input_layout.addWidget(QLabel("Пункт бюджета:"))
        self.item_combo = QComboBox()
        self.populate_budget_items()
        input_layout.addWidget(self.item_combo)
        
        input_layout.addWidget(QLabel("Сумма:"))
        self.vvod_summi = QLineEdit()
        self.vvod_summi.setPlaceholderText("0")
        self.vvod_summi.textChanged.connect(self.proverka_vvoda_summi)
        input_layout.addWidget(self.vvod_summi)
        
        layout.addLayout(input_layout)
        
        self.spendings_list = QListWidget()
        layout.addWidget(QLabel("Добавленные траты:"))
        layout.addWidget(self.spendings_list)
        
        self.update_spendings_list()
        
        button_layout = QHBoxLayout()
        
        self.add_spending_btn = QPushButton("Добавить трату")
        self.add_spending_btn.clicked.connect(self.add_spending)
        button_layout.addWidget(self.add_spending_btn)
        
        self.finish_btn = QPushButton("Завершить")
        self.finish_btn.clicked.connect(self.finish_day)
        button_layout.addWidget(self.finish_btn)

        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def populate_budget_items(self):
        if not self.parent or not self.parent.budget_map_data:
            QMessageBox.warning(self, "Ошибка", "Сначала создайте карту бюджета!")
            self.close()
            return
            
        budget_items = self.parent.budget_map_data['items']
        for item_name, item_summa in budget_items:
            self.item_combo.addItem(f"{item_name} (бюджет: {item_summa} руб.)", item_name)
    
    def proverka_vvoda_summi(self, text):
        cleaned = ''.join(filter(lambda x: x.isdigit() or x == '.', text))
        
        if cleaned.count('.') > 1:
            parts = cleaned.split('.')
            cleaned = parts[0] + '.' + ''.join(parts[1:])
        
        if cleaned != text:
            self.vvod_summi.setText(cleaned)
            self.vvod_summi.setCursorPosition(len(cleaned))
    
    def update_spendings_list(self):
        self.spendings_list.clear()
        for spending in self.daily_spendings:
            spending_text = f"{spending['item_name']} - {spending['summa']:.2f} руб."
            self.spendings_list.addItem(spending_text)
    
    def add_spending(self):
        if self.item_combo.count() == 0:
            QMessageBox.warning(self, "Ошибка", "Нет доступных пунктов бюджета")
            return
            
        summa_text = self.vvod_summi.text().strip()
        if not summa_text:
            QMessageBox.warning(self, "Ошибка", "Введите сумму")
            return
            
        try:
            summa = float(summa_text)
            if summa <= 0:
                QMessageBox.warning(self, "Ошибка", "Сумма должна быть больше 0")
                return
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Некорректная сумма")
            return
        
        selected_index = self.item_combo.currentIndex()
        item_name = self.item_combo.itemData(selected_index)
        display_text = self.item_combo.currentText()
        
        spending_data = {
            'item_name': item_name,
            'summa': summa,
            'display_text': display_text
        }
        self.daily_spendings.append(spending_data)
        
        self.update_spendings_list()
        
        self.vvod_summi.clear()
        
        QMessageBox.information(self, "Успех", f"Трата добавлена: {item_name} - {summa:.2f} руб.")
    
    def finish_day(self):
        if not self.daily_spendings:
            QMessageBox.warning(self, "Ошибка", "Добавьте хотя бы одну трату")
            return
        
        if self.parent:
            self.parent.process_daily_spendings(self.daily_spendings, self.selected_date)
        
        self.accept()


class BudgetMapDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Карта бюджета")
        self.setGeometry(200, 200, 800, 600)
        
        self.total_budget = 0
        self.ostatok_budget = 0
        self.budget_items = []
        self.start_date = None
        self.end_date = None
        self.budget_confirmed = False
        self.period_set = False
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        input_layout = QHBoxLayout()
        
        self.item_name_input = QLineEdit()
        self.item_name_input.setPlaceholderText("Название пункта")
        input_layout.addWidget(QLabel("Пункт:"))
        input_layout.addWidget(self.item_name_input)
        
        self.item_summa_input = QLineEdit()
        self.item_summa_input.setPlaceholderText("Сумма")
        self.item_summa_input.textChanged.connect(self.proverka_vvoda_summi)
        input_layout.addWidget(QLabel("Сумма:"))
        input_layout.addWidget(self.item_summa_input)
        
        layout.addLayout(input_layout)
        
        self.items_list = QListWidget()
        layout.addWidget(QLabel("Добавленные пункты:"))
        layout.addWidget(self.items_list)
        
        bottom_layout = QVBoxLayout()
        
        budget_layout = QHBoxLayout()
        self.budget_input = QLineEdit()
        self.budget_input.setPlaceholderText("Общий бюджет")
        self.budget_input.textChanged.connect(self.proverka_budget_input)
        budget_layout.addWidget(QLabel("Общий бюджет:"))
        budget_layout.addWidget(self.budget_input)
        
        self.confirm_budget_btn = QPushButton("Подтвердить бюджет")
        self.confirm_budget_btn.clicked.connect(self.confirm_budget)
        budget_layout.addWidget(self.confirm_budget_btn)
        
        bottom_layout.addLayout(budget_layout)
        
        period_layout = QHBoxLayout()
        self.period_input = QLineEdit()
        self.period_input.setPlaceholderText("дд.мм.гг-дд.мм.гг")
        self.period_input.textChanged.connect(self.format_period_input)
        period_layout.addWidget(QLabel("Срок карты:"))
        period_layout.addWidget(self.period_input)
        
        self.set_period_btn = QPushButton("Задать срок")
        self.set_period_btn.clicked.connect(self.set_period)
        period_layout.addWidget(self.set_period_btn)
        
        bottom_layout.addLayout(period_layout)
        
        action_layout = QHBoxLayout()
        
        self.add_item_btn = QPushButton("Добавить пункт")
        self.add_item_btn.clicked.connect(self.add_item)
        action_layout.addWidget(self.add_item_btn)
        
        self.finish_map_btn = QPushButton("Закончить карту")
        self.finish_map_btn.clicked.connect(self.finish_map)
        action_layout.addWidget(self.finish_map_btn)
        
        bottom_layout.addLayout(action_layout)
        layout.addLayout(bottom_layout)
        
        self.setLayout(layout)
    
    def proverka_vvoda_summi(self, text):
        cleaned = ''.join(filter(str.isdigit, text))
        if cleaned != text:
            self.item_summa_input.setText(cleaned)
            self.item_summa_input.setCursorPosition(len(cleaned))
    
    def proverka_budget_input(self, text):
        cleaned = ''.join(filter(str.isdigit, text))
        if cleaned != text:
            self.budget_input.setText(cleaned)
            self.budget_input.setCursorPosition(len(cleaned))
    
    def format_period_input(self, text):
        if not text:
            return
            
        digits = ''.join(filter(str.isdigit, text))
        
        formatted = ""
        for i, char in enumerate(digits[:12]):
            if i == 2 or i == 4 or i == 8 or i == 10:
                formatted += "."
            if i == 6:
                formatted += "-"
            formatted += char
        
        if formatted != text:
            self.period_input.setText(formatted)
            self.period_input.setCursorPosition(len(formatted))
    
    def confirm_budget(self):
        if self.budget_input.text():
            self.total_budget = int(self.budget_input.text())
            self.ostatok_budget = self.total_budget
            self.budget_input.setEnabled(False)
            self.confirm_budget_btn.setEnabled(False)
            self.budget_confirmed = True
            QMessageBox.information(self, "Успех", f"Бюджет подтвержден: {self.total_budget}")
    
    def set_period(self):
        period_text = self.period_input.text()
        if len(''.join(filter(str.isdigit, period_text))) == 12:
            try:
                start_str = period_text[:8]
                end_str = period_text[9:]
                
                day_s, month_s, year_s = start_str.split('.')
                day_e, month_e, year_e = end_str.split('.')
                
                start_date = dt.date(2000 + int(year_s), int(month_s), int(day_s))
                end_date = dt.date(2000 + int(year_e), int(month_e), int(day_e))
                
                today = dt.date.today()
                if start_date < today:
                    start_date = today
                    corrected_start = start_date.strftime("%d.%m.%y")
                    self.period_input.setText(f"{corrected_start}-{end_str}")
                
                self.start_date = start_date
                self.end_date = end_date
                self.period_input.setEnabled(False)
                self.set_period_btn.setEnabled(False)
                self.period_set = True
                
                QMessageBox.information(self, "Успех", f"Срок установлен: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}")
                
            except ValueError as e:
                QMessageBox.warning(self, "Ошибка", "Некорректный формат даты")
        else:
            QMessageBox.warning(self, "Ошибка", "Введите полный период в формате дд.мм.гг-дд.мм.гг")
    
    def add_item(self):
        if not self.budget_confirmed:
            QMessageBox.warning(self, "Ошибка", "Сначала подтвердите общий бюджет")
            return
            
        item_name = self.item_name_input.text().strip()
        item_summa_text = self.item_summa_input.text().strip()
        
        if not item_name:
            QMessageBox.warning(self, "Ошибка", "Введите название пункта")
            return
            
        if not item_summa_text:
            QMessageBox.warning(self, "Ошибка", "Введите сумму")
            return
            
        item_summa = int(item_summa_text)
        
        if item_summa > self.ostatok_budget:
            QMessageBox.warning(self, "Ошибка", f"Сумма превышает остаток бюджета ({self.ostatok_budget})")
            return
            
        if item_summa <= 0:
            QMessageBox.warning(self, "Ошибка", "Сумма должна быть больше 0")
            return
        
        self.budget_items.append((item_name, item_summa))
        self.ostatok_budget -= item_summa
        
        item_text = f"{item_name} - {item_summa} руб. (Остаток для распределения: {self.ostatok_budget} руб.)"
        self.items_list.addItem(item_text)
        
        self.item_name_input.clear()
        self.item_summa_input.clear()
        
        QMessageBox.information(self, "Успех", f"Пункт '{item_name}' добавлен")
    
    def finish_map(self):
        if not self.budget_confirmed:
            QMessageBox.warning(self, "Ошибка", "Сначала подтвердите бюджет")
            return
            
        if not self.period_set:
            QMessageBox.warning(self, "Ошибка", "Сначала задайте срок")
            return
            
        if not self.budget_items:
            QMessageBox.warning(self, "Ошибка", "Добавьте хотя бы один пункт")
            return
        
        if self.parent:
            self.parent.budget_map_data = {
                'items': self.budget_items,
                'total_budget': self.total_budget,
                'start_date': self.start_date,
                'end_date': self.end_date,
                'initial_ostatok': self.ostatok_budget,
                'actual_ostatok': self.total_budget
            }
            self.parent.highlight_budget_period()
            self.parent.display_budget_map()
            self.parent.save_budget_map() 
        
        self.accept()
        

class CartSpenndings(QMainWindow):
    def __init__(self):
        super().__init__()
        
        template = '''<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>MainWindow</class>
 <widget class="QMainWindow" name="MainWindow">
  <property name="geometry">
   <rect>
    <x>0</x>
    <y>0</y>
    <width>925</width>
    <height>597</height>
   </rect>
  </property>
  <property name="windowTitle">
   <string>MainWindow</string>
  </property>
  <widget class="QWidget" name="centralwidget">
   <widget class="QWidget" name="gridLayoutWidget_2">
    <property name="geometry">
     <rect>
      <x>0</x>
      <y>0</y>
      <width>931</width>
      <height>571</height>
     </rect>
    </property>
    <layout class="QGridLayout" name="gridLayout_2">
     <item row="1" column="1">
      <widget class="QDateTimeEdit" name="dateTimeEdit"/>
     </item>
     <item row="1" column="0">
      <layout class="QHBoxLayout" name="horizontalLayout">
       <item>
        <widget class="QPushButton" name="pushButton_4">
         <property name="text">
          <string>Составить карту бюджета</string>
         </property>
        </widget>
       </item>
       <item>
        <widget class="QPushButton" name="pushButton_2">
         <property name="text">
          <string>Записать расходы</string>
         </property>
        </widget>
       </item>
       <item>
        <widget class="QPushButton" name="pushButton_3">
         <property name="text">
          <string>Показать траты за день</string>
         </property>
        </widget>
       </item>
       <item>
        <widget class="QPushButton" name="pushButton">
         <property name="text">
          <string>Подвести статистику</string>
         </property>
        </widget>
       </item>
      </layout>
     </item>
     <item row="0" column="0">
      <widget class="QCalendarWidget" name="calendarWidget"/>
     </item>
     <item row="0" column="1">
      <widget class="QListWidget" name="listWidget"/>
     </item>
    </layout>
   </widget>
  </widget>
  <widget class="QMenuBar" name="menubar">
   <property name="geometry">
    <rect>
     <x>0</x>
     <y>0</y>
     <width>925</width>
     <height>19</height>
    </rect>
   </property>
  </widget>
  <widget class="QStatusBar" name="statusbar"/>
 </widget>
 <resources/>
 <connections/>
</ui>
'''
        f = io.StringIO(template)
        uic.loadUi(f, self)

        timedata = dt.datetime.now()
        
        self.calendarWidget = self.findChild(QtWidgets.QCalendarWidget, 'calendarWidget')
        self.timeDataEdit = self.findChild(QtWidgets.QDateTimeEdit, 'dateTimeEdit')
        self.addPunktBtn = self.findChild(QtWidgets.QPushButton, 'pushButton_2')
        self.seeSpendingsBtn = self.findChild(QtWidgets.QPushButton, 'pushButton_3')
        self.endStatisticBtn = self.findChild(QtWidgets.QPushButton, 'pushButton')
        self.doCartBtn = self.findChild(QtWidgets.QPushButton, 'pushButton_4')
        self.eventList = self.findChild(QtWidgets.QListWidget, 'listWidget')
        
        self.timeDataEdit.setEnabled(False)
        
        self.timeDataEdit.setDateTime(QDateTime.currentDateTime())
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000) 

        self.budget_map_data = None
        self.daily_spendings_data = {}
        self.selected_calendar_date = dt.date.today()

        self.doCartBtn.clicked.connect(self.cart_doing)
        self.addPunktBtn.clicked.connect(self.get_day_spendings)
        self.seeSpendingsBtn.clicked.connect(self.show_day_spendings)
        self.endStatisticBtn.clicked.connect(self.final_statistics)
        
        self.calendarWidget.selectionChanged.connect(self.on_calendar_date_selected)

        self.setWindowTitle("Инспектор бюджета")
        
        self.db_manager = DatabaseManager()
        self.load_data()

    def update_time(self):
        self.timeDataEdit.setDateTime(QDateTime.currentDateTime())

    def on_calendar_date_selected(self):
        selected_date = self.calendarWidget.selectedDate()
        self.selected_calendar_date = dt.date(selected_date.year(), selected_date.month(), selected_date.day())

    def cart_doing(self):
        self.clear_old_data()
        
        dialog = BudgetMapDialog(self)
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Успех", "Карта бюджета успешно создана!")
            print("Созданная карта бюджета:", self.budget_map_data)

    def clear_old_data(self):
        self.db_manager.clear_all_data()
        
        try:
            if os.path.exists('budget_map.csv'):
                os.remove('budget_map.csv')
            if os.path.exists('daily_spendings.csv'):
                os.remove('daily_spendings.csv')
            print("CSV файлы очищены")
        except Exception as e:
            print(f"Ошибка при очистке CSV файлов: {e}")
        
        self.budget_map_data = None
        self.daily_spendings_data = {}
        self.eventList.clear()
        
        current_date = self.calendarWidget.minimumDate()
        end_calendar = self.calendarWidget.maximumDate()
        while current_date <= end_calendar:
            self.calendarWidget.setDateTextFormat(current_date, QTextCharFormat())
            current_date = current_date.addDays(1)

    def get_day_spendings(self):
        if not self.budget_map_data:
            QMessageBox.warning(self, "Ошибка", "Сначала создайте карту бюджета!")
            return
            
        dialog = DaySpendingsDialog(self)
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Успех", "Дневные траты успешно учтены!")

    def show_day_spendings(self):
        if not self.budget_map_data:
            QMessageBox.warning(self, "Ошибка", "Сначала создайте карту бюджета!")
            return
            
        dialog = DaySpendingsViewDialog(
            parent=self,
            selected_date=self.selected_calendar_date,
            budget_map_data=self.budget_map_data,
            daily_spendings_data=self.daily_spendings_data
        )
        dialog.exec()

    def final_statistics(self):
        if not self.budget_map_data:
            QMessageBox.warning(self, "Ошибка", "Сначала создайте карту бюджета!")
            return
            
        dialog = StatisticsDialog(
            parent=self,
            budget_map_data=self.budget_map_data,
            daily_spendings_data=self.daily_spendings_data
        )
        dialog.exec()

    def process_daily_spendings(self, spendings, date):
        date_str = date.strftime('%Y-%m-%d')
        
        self.daily_spendings_data[date_str] = spendings
        
        self.display_budget_map()
        
        self.save_daily_spendings(date, spendings)
        
        total_spent = sum(spending['summa'] for spending in spendings)
        QMessageBox.information(self, "Итог дня", 
                               f"За {date.strftime('%d.%m.%Y')} потрачено: {total_spent:.2f} руб.")

    def save_budget_map(self):
        if not self.budget_map_data:
            return
            
        try:
            self.db_manager.save_budget_map(self.budget_map_data)
            print("Карта бюджета сохранена в БД")
            
            self.save_budget_map_to_csv()
            
        except Exception as e:
            print(f"Ошибка при сохранении карты бюджета: {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить карту бюджета: {e}")

    def save_budget_map_to_csv(self):
        try:
            with open('budget_map.csv', 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                
                writer.writerow(['total_budget', 'start_date', 'end_date', 'initial_ostatok'])
                
                writer.writerow([
                    self.budget_map_data['total_budget'],
                    self.budget_map_data['start_date'].strftime('%Y-%m-%d'),
                    self.budget_map_data['end_date'].strftime('%Y-%m-%d'),
                    self.budget_map_data['initial_ostatok']
                ])
                
                writer.writerow([])
                writer.writerow(['budget_items'])
                writer.writerow(['item_name', 'item_summa'])
                
                for item_name, item_summa in self.budget_map_data['items']:
                    writer.writerow([item_name, item_summa])
                    
            print("Карта бюджета сохранена в CSV")
            
        except Exception as e:
            print(f"Ошибка при сохранении карты бюджета в CSV: {e}")

    def save_daily_spendings(self, date, spendings):
        if not spendings:
            return
            
        try:
            self.db_manager.save_daily_spendings(date, spendings)
            print("Дневные траты сохранены в БД")
            
            self.save_daily_spendings_to_csv()
            
        except Exception as e:
            print(f"Ошибка при сохранении дневных трат: {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить дневные траты: {e}")

    def save_daily_spendings_to_csv(self):
        try:
            with open('daily_spendings.csv', 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                
                writer.writerow(['date', 'item_name', 'summa'])
                
                for date_str, spendings_list in self.daily_spendings_data.items():
                    for spending in spendings_list:
                        writer.writerow([
                            date_str,
                            spending['item_name'],
                            spending['summa']
                        ])
                        
            print("Дневные траты сохранены в CSV")
            
        except Exception as e:
            print(f"Ошибка при сохранении дневных трат в CSV: {e}")

    def load_data(self):
        self.load_budget_map()
        self.load_daily_spendings()
        
        if not self.budget_map_data:
            self.load_budget_map_from_csv()
        
        if not self.daily_spendings_data:
            self.load_daily_spendings_from_csv()
        
        if self.budget_map_data:
            self.highlight_budget_period()
            self.display_budget_map()

    def load_budget_map(self):
        try:
            self.budget_map_data = self.db_manager.get_latest_budget_map()
            if self.budget_map_data:
                print("Карта бюджета загружена из БД")
                
        except Exception as e:
            print(f"Ошибка при загрузке карты бюджета: {e}")

    def load_budget_map_from_csv(self):
        try:
            if not os.path.exists('budget_map.csv'):
                return
                
            with open('budget_map.csv', 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                
                next(reader)
                
                main_data = next(reader)
                if not main_data:
                    return
                    
                total_budget = int(main_data[0])
                start_date = dt.datetime.strptime(main_data[1], '%Y-%m-%d').date()
                end_date = dt.datetime.strptime(main_data[2], '%Y-%m-%d').date()
                initial_ostatok = int(main_data[3])
                
                next(reader)
                next(reader)
                next(reader)
                
                budget_items = []
                for row in reader:
                    if row:
                        item_name = row[0]
                        item_summa = int(row[1])
                        budget_items.append((item_name, item_summa))
                
                self.budget_map_data = {
                    'items': budget_items,
                    'total_budget': total_budget,
                    'start_date': start_date,
                    'end_date': end_date,
                    'initial_ostatok': initial_ostatok,
                    'actual_ostatok': total_budget
                }
                
            print("Карта бюджета загружена из CSV")
            
            if self.budget_map_data:
                self.db_manager.save_budget_map(self.budget_map_data)
                print("Данные из CSV перенесены в БД")
                
        except Exception as e:
            print(f"Ошибка при загрузке карты бюджета из CSV: {e}")

    def load_daily_spendings(self):
        try:
            self.daily_spendings_data = self.db_manager.get_all_daily_spendings()
            if self.daily_spendings_data:
                print("Дневные траты загружены из БД")
                
        except Exception as e:
            print(f"Ошибка при загрузке дневных трат: {e}")

    def load_daily_spendings_from_csv(self):
        try:
            if not os.path.exists('daily_spendings.csv'):
                return
                
            with open('daily_spendings.csv', 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                
                next(reader)
                
                self.daily_spendings_data = {}
                for row in reader:
                    if row:
                        date_str = row[0]
                        item_name = row[1]
                        summa = float(row[2])
                        
                        if date_str not in self.daily_spendings_data:
                            self.daily_spendings_data[date_str] = []
                            
                        self.daily_spendings_data[date_str].append({
                            'item_name': item_name,
                            'summa': summa,
                            'display_text': f"{item_name} (бюджет: ... руб.)"
                        })
                
            print("Дневные траты загружены из CSV")
            
            for date_str, spendings in self.daily_spendings_data.items():
                date = dt.datetime.strptime(date_str, '%Y-%m-%d').date()
                self.db_manager.save_daily_spendings(date, spendings)
            print("Данные из CSV перенесены в БД")
                
        except Exception as e:
            print(f"Ошибка при загрузке дневных трат из CSV: {e}")

    def highlight_budget_period(self):
        if not self.budget_map_data:
            return
            
        start_date = self.budget_map_data['start_date']
        end_date = self.budget_map_data['end_date']
        
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QtGui.QColor(173, 216, 230))
        
        current_date = self.calendarWidget.minimumDate()
        end_calendar = self.calendarWidget.maximumDate()
        
        while current_date <= end_calendar:
            self.calendarWidget.setDateTextFormat(current_date, QTextCharFormat())
            current_date = current_date.addDays(1)
        
        current_date = start_date
        while current_date <= end_date:
            qt_date = QtCore.QDate(current_date.year, current_date.month, current_date.day)
            self.calendarWidget.setDateTextFormat(qt_date, highlight_format)
            current_date += dt.timedelta(days=1)

    def display_budget_map(self):
        if not self.budget_map_data:
            return
            
        self.eventList.clear()
        
        title_item = QListWidgetItem("=== КАРТА БЮДЖЕТА ===")
        title_item.setBackground(QtGui.QColor(200, 230, 255))
        self.eventList.addItem(title_item)
        
        start_date = self.budget_map_data['start_date']
        end_date = self.budget_map_data['end_date']
        period_text = f"Период: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}"
        period_item = QListWidgetItem(period_text)
        self.eventList.addItem(period_item)
        
        total_budget = self.budget_map_data['total_budget']
        initial_ostatok = self.budget_map_data['initial_ostatok']
        
        budget_text = f"Общий бюджет: {total_budget} руб."
        budget_item = QListWidgetItem(budget_text)
        self.eventList.addItem(budget_item)
        
        total_spent = self.calculate_total_spent()
        actual_ostatok = total_budget - total_spent
        
        distributed_text = f"Распределено по пунктам: {total_budget - initial_ostatok} руб."
        distributed_item = QListWidgetItem(distributed_text)
        self.eventList.addItem(distributed_item)
        
        ostatok_text = f"Остаток бюджета: {actual_ostatok:.2f} руб."
        ostatok_item = QListWidgetItem(ostatok_text)
        if actual_ostatok < 0:
            ostatok_item.setForeground(QtGui.QColor(255, 0, 0))
        self.eventList.addItem(ostatok_item)
        
        if total_spent > 0:
            spent_text = f"Всего потрачено: {total_spent:.2f} руб."
            spent_item = QListWidgetItem(spent_text)
            spent_item.setForeground(QtGui.QColor(200, 0, 0))
            self.eventList.addItem(spent_text)
        
        separator_item = QListWidgetItem("─" * 30)
        separator_item.setForeground(QtGui.QColor(128, 128, 128))
        self.eventList.addItem(separator_item)
        
        items_title_item = QListWidgetItem("Пункты бюджета:")
        items_title_item.setBackground(QtGui.QColor(230, 230, 230))
        self.eventList.addItem(items_title_item)
        
        budget_items = self.budget_map_data['items']
        for i, (item_name, item_summa) in enumerate(budget_items, 1):
            item_text = f"{i}. {item_name} - {item_summa} руб."
            list_item = QListWidgetItem(item_text)
            self.eventList.addItem(list_item)

    def calculate_total_spent(self):
        total = 0
        for date_str, spendings in self.daily_spendings_data.items():
            total += sum(spending['summa'] for spending in spendings)
        return total


if __name__ == '__main__':
    app = QApplication(sys.argv)
    planner = CartSpenndings()
    planner.show()
    sys.exit(app.exec())