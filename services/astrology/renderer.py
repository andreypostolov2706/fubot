"""
Astrology Service - HTML Renderer
Рендерит HTML шаблоны и сохраняет как HTML файлы
"""
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Optional

from jinja2 import Environment, FileSystemLoader

from loguru import logger


TEMPLATES_DIR = Path(__file__).parent / "templates"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "renders"


def sanitize_filename(name: str) -> str:
    """Очищает имя файла от недопустимых символов"""
    # Заменяем недопустимые символы на подчёркивание
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    return name.strip()


class AstrologyRenderer:
    """Рендерер астрологических ответов в HTML"""
    
    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=True
        )
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def _get_bot_link(self) -> Optional[str]:
        bot_link = os.getenv("TELEGRAM_BOT_LINK") or os.getenv("BOT_LINK")
        if bot_link:
            return bot_link

        username = os.getenv("TELEGRAM_BOT_USERNAME") or os.getenv("BOT_USERNAME")
        if username:
            username = username.lstrip("@").strip()
            if username:
                return f"https://t.me/{username}"

        return None
    
    def _markdown_to_html(self, text: str) -> str:
        """Конвертирует markdown/текст в HTML"""
        if not text:
            return ""
        
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        
        text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
        text = re.sub(r'^# (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
        
        lines = text.split('\n')
        result = []
        in_list = False
        
        for line in lines:
            stripped = line.strip()
            
            if stripped.startswith('- ') or stripped.startswith('• '):
                if not in_list:
                    result.append('<ul>')
                    in_list = True
                item = stripped[2:].strip()
                result.append(f'<li>{item}</li>')
            elif stripped.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                if not in_list:
                    result.append('<ol>')
                    in_list = True
                item = re.sub(r'^\d+\.\s*', '', stripped)
                result.append(f'<li>{item}</li>')
            else:
                if in_list:
                    if result[-1].startswith('<ol>') or '<ol>' in ''.join(result[-5:]):
                        result.append('</ol>')
                    else:
                        result.append('</ul>')
                    in_list = False
                
                if stripped and not stripped.startswith('<'):
                    result.append(f'<p>{stripped}</p>')
                elif stripped:
                    result.append(stripped)
        
        if in_list:
            result.append('</ul>')
        
        return '\n'.join(result)
    
    def render_natal(
        self,
        content: str,
        sun_sign: str,
        moon_sign: str,
        asc_sign: str,
        user_id: int,
        person_name: str = ""
    ) -> Optional[str]:
        """Рендерит натальную карту в HTML файл"""
        title = f"Натальная карта {person_name}".strip() if person_name else "Натальная карта"
        try:
            template = self.env.get_template("natal_chart.html")
            
            html_content = self._markdown_to_html(content)
            
            html = template.render(
                title=title,
                sun_sign=sun_sign,
                moon_sign=moon_sign,
                asc_sign=asc_sign,
                content=html_content,
                date=datetime.now().strftime("%d.%m.%Y"),
                bot_link=self._get_bot_link(),
            )
            
            # Формируем понятное имя файла
            filename = sanitize_filename(title)
            output_path = OUTPUT_DIR / f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            logger.info(f"Rendered natal chart to {output_path}")
            return str(output_path)
        except Exception as e:
            logger.error(f"Error rendering natal chart: {e}")
            return self.render_generic(title=title, content=content, user_id=user_id)
    
    def render_daily(
        self,
        content: str,
        sun_sign: str,
        sun_emoji: str,
        user_id: int,
        person_name: str = ""
    ) -> Optional[str]:
        """Рендерит ежедневный гороскоп в HTML файл"""
        date_str = datetime.now().strftime("%d.%m.%Y")
        title = f"Гороскоп {person_name} на {date_str}".strip() if person_name else f"Гороскоп на {date_str}"
        try:
            template = self.env.get_template("daily.html")
            
            html_content = self._markdown_to_html(content)
            
            html = template.render(
                title=title,
                sun_sign=sun_sign,
                sun_emoji=sun_emoji,
                date_formatted=datetime.now().strftime("%d %B %Y"),
                content=html_content,
                date=date_str,
                bot_link=self._get_bot_link(),
            )
            
            # Формируем понятное имя файла
            filename = sanitize_filename(title)
            output_path = OUTPUT_DIR / f"{filename}.html"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            logger.info(f"Rendered daily horoscope to {output_path}")
            return str(output_path)
        except Exception as e:
            logger.error(f"Error rendering daily horoscope: {e}")
            return self.render_generic(title=title, content=content, user_id=user_id)
    
    def render_compatibility(
        self,
        content: str,
        person1_name: str,
        person1_emoji: str,
        person2_name: str,
        person2_emoji: str,
        user_id: int
    ) -> Optional[str]:
        """Рендерит совместимость в HTML файл"""
        title = f"Совместимость {person1_name} и {person2_name}"
        try:
            template = self.env.get_template("compatibility.html")
            
            html_content = self._markdown_to_html(content)
            
            html = template.render(
                title=title,
                person1_name=person1_name,
                person1_emoji=person1_emoji,
                person2_name=person2_name,
                person2_emoji=person2_emoji,
                content=html_content,
                date=datetime.now().strftime("%d.%m.%Y"),
                bot_link=self._get_bot_link(),
            )
            
            # Формируем понятное имя файла
            filename = sanitize_filename(title)
            output_path = OUTPUT_DIR / f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            logger.info(f"Rendered compatibility to {output_path}")
            return str(output_path)
        except Exception as e:
            logger.error(f"Error rendering compatibility: {e}")
            return self.render_generic(title=title, content=content, user_id=user_id)
    
    def render_child(
        self,
        content: str,
        child_name: str,
        child_age: int,
        sun_sign: str,
        moon_sign: str,
        user_id: int
    ) -> Optional[str]:
        """Рендерит детский гороскоп в HTML файл"""
        title = f"Детский гороскоп {child_name}"
        try:
            template = self.env.get_template("child.html")
            
            html_content = self._markdown_to_html(content)
            
            html = template.render(
                title=title,
                child_name=child_name,
                child_age=child_age,
                sun_sign=sun_sign,
                moon_sign=moon_sign,
                content=html_content,
                date=datetime.now().strftime("%d.%m.%Y"),
                bot_link=self._get_bot_link(),
            )
            
            # Формируем понятное имя файла
            filename = sanitize_filename(title)
            output_path = OUTPUT_DIR / f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            logger.info(f"Rendered child horoscope to {output_path}")
            return str(output_path)
        except Exception as e:
            logger.error(f"Error rendering child horoscope: {e}")
            return self.render_generic(title=title, content=content, user_id=user_id)
    
    def render_question(
        self,
        content: str,
        question_text: str,
        persons: list,  # [{"name": "Андрей", "emoji": "♈"}]
        user_id: int
    ) -> Optional[str]:
        """Рендерит вопрос астрологу в HTML файл"""
        title = "Ответ астролога"
        try:
            template = self.env.get_template("question.html")
            
            html_content = self._markdown_to_html(content)
            
            names = [p.get("name") for p in persons if p.get("name")]
            if len(names) == 1:
                title = f"Ответ астролога для {names[0]}"
            else:
                title = f"Ответ астролога ({', '.join(names)})"
            
            html = template.render(
                title=title,
                question_text=question_text,
                persons=persons,
                content=html_content,
                date=datetime.now().strftime("%d.%m.%Y"),
                bot_link=self._get_bot_link(),
            )
            
            # Формируем понятное имя файла
            filename = sanitize_filename(f"Вопрос астрологу {' '.join(names)}")
            output_path = OUTPUT_DIR / f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            logger.info(f"Rendered question answer to {output_path}")
            return str(output_path)
        except Exception as e:
            logger.error(f"Error rendering question answer: {e}")
            return self.render_generic(title=title, content=content, user_id=user_id)

    def render_generic(
        self,
        title: str,
        content: str,
        user_id: int,
        icon: str = "✨",
        subtitle: str = "",
    ) -> Optional[str]:
        """Рендерит произвольный результат в HTML файл используя шаблон generic.html."""
        try:
            html_content = self._markdown_to_html(content)
            date_str = datetime.now().strftime("%d.%m.%Y")
            
            if not subtitle:
                subtitle = date_str

            template = self.env.get_template('generic.html')
            html = template.render(
                title=title,
                icon=icon,
                subtitle=subtitle,
                content=html_content,
            )

            filename = sanitize_filename(title)
            output_path = OUTPUT_DIR / f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)

            logger.info(f"Rendered generic html to {output_path}")
            return str(output_path)
        except Exception as e:
            logger.error(f"Error rendering generic html: {e}")
            return None


renderer = AstrologyRenderer()
