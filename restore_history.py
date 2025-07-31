#!/usr/bin/env python3
"""
Скрипт для восстановления истории агента из различных источников
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from flask_app import create_app, db
from flask_app.models import SessionLog


class HistoryRestorer:
    """Класс для восстановления истории диалогов агента"""
    
    def __init__(self):
        self.app = create_app()
        
    def restore_from_json(self, json_file: str) -> int:
        """
        Восстановление истории из JSON файла
        
        Ожидаемый формат JSON:
        [
            {
                "user_id": 123456789,
                "query": "Вопрос пользователя",
                "response": "Ответ агента",
                "timestamp": "2024-01-01T12:00:00" (опционально)
            }
        ]
        """
        if not os.path.exists(json_file):
            print(f"Файл {json_file} не найден")
            return 0
            
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            restored_count = 0
            with self.app.app_context():
                for entry in data:
                    if self._validate_entry(entry):
                        timestamp = None
                        if 'timestamp' in entry:
                            timestamp = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                        
                        log = SessionLog(
                            user_id=entry['user_id'],
                            query=entry['query'][:2000],  # Обрезаем для SQLite
                            response=entry['response'][:2000],
                            timestamp=timestamp or datetime.utcnow()
                        )
                        db.session.add(log)
                        restored_count += 1
                
                db.session.commit()
                
            print(f"Восстановлено {restored_count} записей из {json_file}")
            return restored_count
            
        except Exception as e:
            print(f"Ошибка при восстановлении из JSON: {e}")
            return 0
    
    def restore_from_telegram_export(self, export_file: str, user_id: int) -> int:
        """
        Восстановление из экспорта Telegram
        
        Поддерживает формат JSON экспорта Telegram Desktop
        """
        if not os.path.exists(export_file):
            print(f"Файл экспорта {export_file} не найден")
            return 0
            
        try:
            with open(export_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            messages = data.get('messages', [])
            restored_count = 0
            
            with self.app.app_context():
                for i in range(0, len(messages) - 1, 2):
                    user_msg = messages[i]
                    bot_msg = messages[i + 1] if i + 1 < len(messages) else None
                    
                    if (user_msg.get('from') != 'user' or 
                        not bot_msg or 
                        bot_msg.get('from') == 'user'):
                        continue
                    
                    query = user_msg.get('text', '')
                    response = bot_msg.get('text', '')
                    
                    if query and response:
                        timestamp = datetime.fromisoformat(
                            user_msg.get('date', datetime.utcnow().isoformat())
                        )
                        
                        log = SessionLog(
                            user_id=user_id,
                            query=query[:2000],
                            response=response[:2000],
                            timestamp=timestamp
                        )
                        db.session.add(log)
                        restored_count += 1
                
                db.session.commit()
                
            print(f"Восстановлено {restored_count} диалогов из экспорта Telegram")
            return restored_count
            
        except Exception as e:
            print(f"Ошибка при восстановлении из экспорта Telegram: {e}")
            return 0
    
    def restore_from_logs(self, log_file: str) -> int:
        """
        Восстановление из файлов логов
        
        Ожидаемый формат лога:
        [timestamp] USER user_id: query
        [timestamp] BOT: response
        """
        if not os.path.exists(log_file):
            print(f"Файл логов {log_file} не найден")
            return 0
            
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            restored_count = 0
            current_user_id = None
            current_query = None
            current_timestamp = None
            
            with self.app.app_context():
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    if 'USER' in line and ':' in line:
                        # Парсинг пользовательского сообщения
                        parts = line.split(':', 2)
                        if len(parts) >= 3:
                            try:
                                user_part = parts[1].strip().split()
                                current_user_id = int(user_part[-1])
                                current_query = parts[2].strip()
                                current_timestamp = datetime.now()
                            except:
                                continue
                    
                    elif 'BOT:' in line and current_user_id and current_query:
                        # Парсинг ответа бота
                        response = line.split('BOT:', 1)[1].strip()
                        
                        log = SessionLog(
                            user_id=current_user_id,
                            query=current_query[:2000],
                            response=response[:2000],
                            timestamp=current_timestamp
                        )
                        db.session.add(log)
                        restored_count += 1
                        
                        # Сброс состояния
                        current_user_id = None
                        current_query = None
                        current_timestamp = None
                
                db.session.commit()
                
            print(f"Восстановлено {restored_count} записей из логов")
            return restored_count
            
        except Exception as e:
            print(f"Ошибка при восстановлении из логов: {e}")
            return 0
    
    def backup_current_history(self, backup_file: str = None) -> str:
        """Создание резервной копии текущей истории"""
        if not backup_file:
            backup_file = f"history_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with self.app.app_context():
                logs = SessionLog.query.order_by(SessionLog.timestamp).all()
                
                data = []
                for log in logs:
                    data.append({
                        'user_id': log.user_id,
                        'query': log.query,
                        'response': log.response,
                        'timestamp': log.timestamp.isoformat()
                    })
                
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                print(f"Резервная копия сохранена в {backup_file} ({len(logs)} записей)")
                return backup_file
                
        except Exception as e:
            print(f"Ошибка при создании резервной копии: {e}")
            return ""
    
    def get_history_stats(self) -> Dict:
        """Получение статистики по истории"""
        try:
            with self.app.app_context():
                total_logs = SessionLog.query.count()
                unique_users = db.session.query(SessionLog.user_id).distinct().count()
                
                oldest_log = SessionLog.query.order_by(SessionLog.timestamp).first()
                newest_log = SessionLog.query.order_by(SessionLog.timestamp.desc()).first()
                
                stats = {
                    'total_conversations': total_logs,
                    'unique_users': unique_users,
                    'oldest_record': oldest_log.timestamp.isoformat() if oldest_log else None,
                    'newest_record': newest_log.timestamp.isoformat() if newest_log else None
                }
                
                return stats
                
        except Exception as e:
            print(f"Ошибка при получении статистики: {e}")
            return {}
    
    def clear_history(self, confirm: bool = False) -> bool:
        """Очистка всей истории (с подтверждением)"""
        if not confirm:
            print("Для очистки истории передайте confirm=True")
            return False
            
        try:
            with self.app.app_context():
                deleted_count = SessionLog.query.count()
                SessionLog.query.delete()
                db.session.commit()
                
                print(f"Удалено {deleted_count} записей из истории")
                return True
                
        except Exception as e:
            print(f"Ошибка при очистке истории: {e}")
            return False
    
    def _validate_entry(self, entry: Dict) -> bool:
        """Валидация записи для восстановления"""
        required_fields = ['user_id', 'query', 'response']
        return all(field in entry and entry[field] for field in required_fields)


def main():
    """Интерактивное меню для восстановления истории"""
    restorer = HistoryRestorer()
    
    print("=== Восстановление истории агента ===")
    print("1. Восстановить из JSON файла")
    print("2. Восстановить из экспорта Telegram")
    print("3. Восстановить из файлов логов")
    print("4. Создать резервную копию текущей истории")
    print("5. Показать статистику истории")
    print("6. Очистить историю")
    print("0. Выход")
    
    while True:
        choice = input("\nВыберите действие (0-6): ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            file_path = input("Путь к JSON файлу: ").strip()
            restorer.restore_from_json(file_path)
        elif choice == '2':
            file_path = input("Путь к файлу экспорта Telegram: ").strip()
            user_id = int(input("ID пользователя: ").strip())
            restorer.restore_from_telegram_export(file_path, user_id)
        elif choice == '3':
            file_path = input("Путь к файлу логов: ").strip()
            restorer.restore_from_logs(file_path)
        elif choice == '4':
            backup_file = input("Имя файла резервной копии (Enter для автоматического): ").strip()
            if not backup_file:
                backup_file = None
            restorer.backup_current_history(backup_file)
        elif choice == '5':
            stats = restorer.get_history_stats()
            print("\n=== Статистика истории ===")
            for key, value in stats.items():
                print(f"{key}: {value}")
        elif choice == '6':
            confirm = input("Вы уверены, что хотите очистить всю историю? (yes/no): ").strip()
            if confirm.lower() == 'yes':
                restorer.clear_history(confirm=True)
        else:
            print("Неверный выбор. Попробуйте снова.")


if __name__ == "__main__":
    main()