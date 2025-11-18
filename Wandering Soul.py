import sys
import math
import random
import time
import os
import json
import datetime

import pygame
from pygame.locals import *

import scripts.spritesheet_loader as spritesheet_loader
import scripts.tile_map as tile_map
import scripts.anim_loader as anim_loader
import scripts.particles as particles_m
from scripts.entity import Entity
import scripts.text as text
from scripts.clip import clip

TILE_SIZE = 12

# Try to initialize audio, if fails use dummy driver
audio_enabled = True
try:
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    # Test if mixer is actually working
    pygame.mixer.get_init()
except:
    # Audio hardware not available, use dummy driver
    os.environ['SDL_AUDIODRIVER'] = 'dummy'
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    audio_enabled = False
    print("Audio not available - running in silent mode")
pygame.display.set_caption('NetGuardian - The Last Firewall')
screen = pygame.display.set_mode((900, 600), pygame.SCALED + pygame.RESIZABLE)
pygame.mouse.set_visible(True)
display = pygame.Surface((300, 200))
clock = pygame.time.Clock()

# ============= COLORES CIBERSEGURIDAD =============
CYBER_COLORS = {
    'primary_green': (0, 255, 100),
    'primary_cyan': (0, 200, 255),
    'safe': (0, 255, 0),
    'warning': (255, 200, 0),
    'danger': (255, 50, 50),
    'bg_dark': (10, 10, 25),
}

# ============= MENSAJES CIBERSEGURIDAD =============
CYBER_MESSAGES = {
    'need_firewall': 'Necesito mas poder de procesamiento!',
    'exit_up': 'El nodo seguro esta arriba...',
    'remote_scan': 'Puedo escanear con mi sonda.',
    'trap': 'Esto parece una trampa...',
    'survive': 'Solo debo sobrevivir.',
    'clear': 'Red estabilizada.',
    'threat': 'Amenaza critica detectada...',
    'more_attacks': 'Mas patrones de ataque?',
    'silence': '...',
    'move_on': 'Debo seguir adelante...',
}

# ============= HISTORIA Y OBJETIVOS DEL JUEGO =============
GAME_STORY = {
    'intro': [
        'ANO 2084 - CRISIS GLOBAL DE SEGURIDAD',
        '',
        'Una amenaza desconocida ha comprometido',
        'la infraestructura digital mundial.',
        '',
        'Tu eres el ultimo Guardian de Red,',
        'un agente especializado en neutralizar',
        'amenazas ciberneticas.',
        '',
        'TU MISION: Restaurar la seguridad de',
        '4 sectores criticos de la red global.',
        '',
        'HERRAMIENTAS:',
        '- FIREWALLS: Recursos computacionales',
        '- SONDA REMOTA: Explora areas peligrosas',
        '- TERMINALES: Resuelve desafios',
        '',
        '[Presiona ESPACIO para comenzar]'
    ]
}

LEVEL_OBJECTIVES = {
    'level_1': {
        'title': 'SECTOR 1: ZONA DE ENTRENAMIENTO',
        'objectives': [
            '1. Aprende los controles basicos',
            '2. Recolecta 1 firewall (recurso)',
            '3. Habla con los NPCs (tecla E)',
            '4. Usa tu sonda remota (flecha abajo)',
            '5. Alcanza el puerto seguro'
        ],
        'concept': 'CONCEPTO: Los firewalls son barreras de seguridad\nque protegen redes de accesos no autorizados.'
    },
    'level_2': {
        'title': 'SECTOR 2: TRAFICO MALICIOSO',
        'objectives': [
            '1. Esquiva los paquetes maliciosos',
            '2. Encuentra y habla con los NPCs',
            '3. Resuelve el desafio de protocolo',
            '4. Sobrevive a las oleadas de ataques',
            '5. Accede al puerto seguro'
        ],
        'concept': 'CONCEPTO: HTTPS es el protocolo seguro de internet.\nEncripta la comunicacion entre navegador y servidor.'
    },
    'level_3': {
        'title': 'SECTOR 3: AMENAZA PERSISTENTE',
        'objectives': [
            '1. Enfrenta al servidor comprometido',
            '2. Aprende sobre encriptacion',
            '3. Usa tus recursos estrategicamente',
            '4. Neutraliza la amenaza avanzada',
            '5. Restaura la seguridad del sector'
        ],
        'concept': 'CONCEPTO: La encriptacion protege datos\ntransformandolos en codigo ilegible sin la clave.'
    },
    'level_4': {
        'title': 'SECTOR 4: NUCLEO DEL SISTEMA',
        'objectives': [
            '1. Alcanza el nucleo central',
            '2. Completa el desafio final',
            '3. Restaura la seguridad global',
            '4. Conviertete en el Guardian definitivo'
        ],
        'concept': 'CONCEPTO: La seguridad en capas combina\nmultiples defensas para proteccion robusta.'
    }
}

# ============= SISTEMA DE HISTORIAL =============
class GameHistory:
    def __init__(self):
        self.history_file = 'data/game_history.json'
        self.current_session = {
            'player_name': '',
            'start_time': 0,
            'threats_neutralized': 0,
            'firewalls_collected': 0,
            'breaches': 0
        }
        self.load_history()
    
    def load_history(self):
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                self.history = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.history = []
            os.makedirs('data', exist_ok=True)
    
    def save_history(self):
        try:
            os.makedirs('data', exist_ok=True)
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando historial: {e}")
    
    def start_session(self, player_name):
        self.current_session = {
            'player_name': player_name,
            'start_time': datetime.datetime.now().isoformat(),
            'threats_neutralized': 0,
            'firewalls_collected': 0,
            'breaches': 0,
            'levels_completed': []
        }
    
    def end_session(self, final_level):
        end_time = datetime.datetime.now()
        start_time = datetime.datetime.fromisoformat(self.current_session['start_time'])
        duration = (end_time - start_time).total_seconds()
        
        session_data = {
            'player_name': self.current_session['player_name'],
            'date': end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'duration_seconds': int(duration),
            'duration_formatted': self.format_duration(duration),
            'threats_neutralized': self.current_session['threats_neutralized'],
            'firewalls_collected': self.current_session['firewalls_collected'],
            'breaches': self.current_session['breaches'],
            'final_level': final_level,
            'levels_completed': self.current_session['levels_completed']
        }
        
        self.history.append(session_data)
        self.save_history()
    
    def format_duration(self, seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def add_threat_neutralized(self):
        self.current_session['threats_neutralized'] += 1
    
    def add_firewall_collected(self):
        self.current_session['firewalls_collected'] += 1
    
    def add_breach(self):
        self.current_session['breaches'] += 1
    
    def add_level_completed(self, level_name):
        if level_name not in self.current_session['levels_completed']:
            self.current_session['levels_completed'].append(level_name)


# ============= SISTEMA DE MENÚ =============
class Button:
    def __init__(self, x, y, width, height, text, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.hovered = False
        self.color_normal = (20, 40, 60)
        self.color_hover = (30, 60, 90)
        self.color_border = CYBER_COLORS['primary_cyan']
    
    def draw(self, surface):
        color = self.color_hover if self.hovered else self.color_normal
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, self.color_border, self.rect, 2)
        
        text_width = self.font.width(self.text)
        text_x = self.rect.centerx - text_width // 2
        text_y = self.rect.centery - 4
        self.font.render(self.text, surface, (text_x, text_y))
    
    def check_hover(self, mouse_pos):
        scaled_pos = (mouse_pos[0] * display.get_width() // screen.get_width(),
                     mouse_pos[1] * display.get_height() // screen.get_height())
        self.hovered = self.rect.collidepoint(scaled_pos)
        return self.hovered
    
    def check_click(self, mouse_pos, mouse_pressed):
        scaled_pos = (mouse_pos[0] * display.get_width() // screen.get_width(),
                     mouse_pos[1] * display.get_height() // screen.get_height())
        if self.rect.collidepoint(scaled_pos) and mouse_pressed:
            return True
        return False


class VolumeControl:
    def __init__(self, x, y, font):
        self.x = x
        self.y = y
        self.font = font
        try:
            self.volume = pygame.mixer.music.get_volume()
        except:
            self.volume = 0.5
        self.plus_button = Button(x + 50, y, 20, 20, '+', font)
        self.minus_button = Button(x + 20, y, 20, 20, '-', font)
    
    def draw(self, surface):
        volume_text = f'{int(self.volume * 100)}'
        self.font.render(volume_text, surface, (self.x, self.y + 5))
        self.plus_button.draw(surface)
        self.minus_button.draw(surface)
    
    def update(self, mouse_pos, mouse_pressed):
        self.plus_button.check_hover(mouse_pos)
        self.minus_button.check_hover(mouse_pos)
        
        if self.plus_button.check_click(mouse_pos, mouse_pressed):
            self.volume = min(1.0, self.volume + 0.1)
            try:
                pygame.mixer.music.set_volume(self.volume)
            except:
                pass
            return True
        
        if self.minus_button.check_click(mouse_pos, mouse_pressed):
            self.volume = max(0.0, self.volume - 0.1)
            try:
                pygame.mixer.music.set_volume(self.volume)
            except:
                pass
            return True
        
        return False


class InputBox:
    def __init__(self, x, y, width, height, font, max_length=15):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.text = ''
        self.max_length = max_length
        self.active = False
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            scaled_pos = (event.pos[0] * display.get_width() // screen.get_width(),
                         event.pos[1] * display.get_height() // screen.get_height())
            self.active = self.rect.collidepoint(scaled_pos)
        
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                self.active = False
            elif len(self.text) < self.max_length:
                char = event.unicode
                if char.isprintable() and (char.isalnum() or char == ' '):
                    self.text += char
    
    def draw(self, surface, game_time):
        color = (30, 60, 90) if self.active else (20, 40, 60)
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, CYBER_COLORS['primary_cyan'], self.rect, 2)
        
        display_text = self.text if self.text else 'Usuario...'
        text_color = CYBER_COLORS['primary_green'] if self.text else (100, 100, 100)
        
        temp_font = text.Font('data/fonts/small_font.png', text_color)
        temp_font.render(display_text, surface, (self.rect.x + 5, self.rect.y + 5))
        
        if self.active and game_time % 30 < 15:
            cursor_x = self.rect.x + 5 + self.font.width(self.text)
            pygame.draw.rect(surface, CYBER_COLORS['primary_green'], 
                           (cursor_x, self.rect.y + 5, 2, 10))


class MenuState:
    MAIN = 0
    HISTORY = 1
    NAME_INPUT = 2
    STORY = 3


class GameMenu:
    def __init__(self, display, font):
        self.display = display
        self.font = font
        self.state = MenuState.MAIN
        self.history = GameHistory()
        
        center_x = display.get_width() // 2
        button_width = 120
        button_height = 25
        
        self.start_button = Button(center_x - button_width // 2, 100, 
                                   button_width, button_height, 'INICIAR', font)
        self.history_button = Button(center_x - button_width // 2, 135, 
                                     button_width, button_height, 'HISTORIAL', font)
        self.exit_button = Button(center_x - button_width // 2, 170, 
                                  button_width, button_height, 'SALIR', font)
        
        self.volume_control = VolumeControl(display.get_width() - 80, 10, font)
        self.name_input = InputBox(center_x - 70, 100, 140, 20, font)
        self.confirm_button = Button(center_x - 40, 130, 80, 20, 'CONECTAR', font)
        self.back_button = Button(10, display.get_height() - 30, 60, 20, 'VOLVER', font)
        
        self.history_scroll = 0
        self.max_history_display = 8
        self.clicked_last_frame = False
    
    def render_cyber_background(self, game_time):
        self.display.fill(CYBER_COLORS['bg_dark'])
        
        grid_color = (0, 50, 80)
        for x in range(0, self.display.get_width(), 20):
            alpha = abs(math.sin(game_time * 0.01 + x * 0.1))
            if alpha > 0.5:
                pygame.draw.line(self.display, grid_color, (x, 0), (x, self.display.get_height()), 1)
        
        for y in range(0, self.display.get_height(), 20):
            alpha = abs(math.sin(game_time * 0.01 + y * 0.1))
            if alpha > 0.5:
                pygame.draw.line(self.display, grid_color, (0, y), (self.display.get_width(), y), 1)
    
    def draw_main_menu(self, game_time):
        self.render_cyber_background(game_time)
        
        title = 'NETGUARDIAN'
        title_x = self.display.get_width() // 2 - self.font.width(title) // 2
        
        glitch_offset = random.randint(-1, 1) if game_time % 60 < 2 else 0
        
        black_font = text.Font('data/fonts/small_font.png', (0, 0, 1))
        cyan_font = text.Font('data/fonts/small_font.png', CYBER_COLORS['primary_cyan'])
        green_font = text.Font('data/fonts/small_font.png', CYBER_COLORS['primary_green'])
        
        black_font.render(title, self.display, (title_x + 1, 31))
        cyan_font.render(title, self.display, (title_x + glitch_offset, 30))
        green_font.render(title, self.display, (title_x, 29))
        
        subtitle = 'THE LAST FIREWALL'
        sub_x = self.display.get_width() // 2 - self.font.width(subtitle) // 2
        small_font = text.Font('data/fonts/small_font.png', CYBER_COLORS['primary_cyan'])
        small_font.render(subtitle, self.display, (sub_x, 45))
        
        for i in range(3):
            x = title_x + i * 60 + 10
            y = 60 + math.sin(game_time * 0.1 + i) * 3
            self.render_firewall_icon([x, y], game_time + i * 20)
        
        self.start_button.draw(self.display)
        self.history_button.draw(self.display)
        self.exit_button.draw(self.display)
        self.volume_control.draw(self.display)
        
        instructions = '> Flechas para navegar'
        inst_x = self.display.get_width() // 2 - self.font.width(instructions) // 2
        inst_font = text.Font('data/fonts/small_font.png', (100, 150, 100))
        inst_font.render(instructions, self.display, (inst_x, self.display.get_height() - 20))
    
    def render_firewall_icon(self, pos, offset):
        points = []
        for i in range(6):
            angle = offset / 30 + i / 6 * math.pi * 2
            radius = 4 + math.sin(offset / 10) * 0.5
            x = pos[0] + math.cos(angle) * radius
            y = pos[1] + math.sin(angle) * radius
            points.append([x, y])
        
        pygame.draw.polygon(self.display, CYBER_COLORS['primary_green'], points, 1)
        pygame.draw.circle(self.display, CYBER_COLORS['primary_cyan'], (int(pos[0]), int(pos[1])), 2, 1)
    
    def draw_name_input(self, game_time):
        self.render_cyber_background(game_time)
        
        prompt = 'ID DE USUARIO:'
        prompt_x = self.display.get_width() // 2 - self.font.width(prompt) // 2
        cyan_font = text.Font('data/fonts/small_font.png', CYBER_COLORS['primary_cyan'])
        cyan_font.render(prompt, self.display, (prompt_x, 70))
        
        self.name_input.draw(self.display, game_time)
        
        if self.name_input.text:
            self.confirm_button.draw(self.display)
    
    def draw_history(self):
        self.render_cyber_background(0)
        
        title = 'HISTORIAL DE SESIONES'
        title_x = self.display.get_width() // 2 - self.font.width(title) // 2
        cyan_font = text.Font('data/fonts/small_font.png', CYBER_COLORS['primary_cyan'])
        cyan_font.render(title, self.display, (title_x, 10))
        
        pygame.draw.line(self.display, CYBER_COLORS['primary_cyan'], 
                        (10, 25), (self.display.get_width() - 10, 25), 1)
        
        if not self.history.history:
            no_data = 'SIN REGISTROS'
            no_data_x = self.display.get_width() // 2 - self.font.width(no_data) // 2
            green_font = text.Font('data/fonts/small_font.png', CYBER_COLORS['primary_green'])
            green_font.render(no_data, self.display, (no_data_x, 100))
        else:
            y_offset = 35
            visible_history = self.history.history[self.history_scroll:
                                                   self.history_scroll + self.max_history_display]
            
            for i, session in enumerate(visible_history):
                if i % 2 == 0:
                    pygame.draw.rect(self.display, (15, 25, 35), 
                                   (5, y_offset - 2, self.display.get_width() - 10, 18))
                
                player_name = session['player_name'][:12]
                duration = session['duration_formatted']
                
                # Soporte para formatos antiguos y nuevos
                threats = session.get('threats_neutralized', session.get('enemies_defeated', 0))
                threats = str(threats)
                
                data_font = text.Font('data/fonts/small_font.png', CYBER_COLORS['primary_green'])
                
                data_font.render(f'{player_name}', self.display, (10, y_offset))
                data_font.render(f'{duration}', self.display, (100, y_offset))
                data_font.render(f'T:{threats}', self.display, (170, y_offset))
                
                date_font = text.Font('data/fonts/small_font.png', (80, 120, 120))
                date_font.render(session['date'][11:16], self.display, (220, y_offset))
                
                y_offset += 18
            
            if len(self.history.history) > self.max_history_display:
                scroll_text = f'{self.history_scroll + 1}-{min(self.history_scroll + self.max_history_display, len(self.history.history))} / {len(self.history.history)}'
                scroll_x = self.display.get_width() // 2 - self.font.width(scroll_text) // 2
                small_font = text.Font('data/fonts/small_font.png', (80, 100, 100))
                small_font.render(scroll_text, self.display, (scroll_x, y_offset + 5))
        
        self.back_button.draw(self.display)
    
    def draw_story(self, game_time):
        self.render_cyber_background(game_time)
        
        y_offset = 15
        for line in GAME_STORY['intro']:
            if line == '':
                y_offset += 8
            elif line.startswith('ANO') or line.startswith('TU MISION') or line.startswith('HERRAMIENTAS'):
                cyan_font = text.Font('data/fonts/small_font.png', CYBER_COLORS['primary_cyan'])
                line_x = self.display.get_width() // 2 - self.font.width(line) // 2
                cyan_font.render(line, self.display, (line_x, y_offset))
                y_offset += 12
            elif line.startswith('['):
                green_font = text.Font('data/fonts/small_font.png', CYBER_COLORS['primary_green'])
                line_x = self.display.get_width() // 2 - self.font.width(line) // 2
                glow = abs(math.sin(game_time * 0.1)) * 20
                glow_color = (0, int(255 - glow), int(100 + glow))
                glow_font = text.Font('data/fonts/small_font.png', glow_color)
                glow_font.render(line, self.display, (line_x, y_offset))
                y_offset += 12
            else:
                white_font = text.Font('data/fonts/small_font.png', (200, 200, 200))
                line_x = self.display.get_width() // 2 - self.font.width(line) // 2
                white_font.render(line, self.display, (line_x, y_offset))
                y_offset += 10
    
    def update(self, game_time, events, mouse_pos, mouse_pressed):
        single_click = mouse_pressed and not self.clicked_last_frame
        self.clicked_last_frame = mouse_pressed
        
        self.volume_control.update(mouse_pos, single_click)
        
        if self.state == MenuState.MAIN:
            self.start_button.check_hover(mouse_pos)
            self.history_button.check_hover(mouse_pos)
            self.exit_button.check_hover(mouse_pos)
            
            if self.start_button.check_click(mouse_pos, single_click):
                self.state = MenuState.STORY
                return 'story'
            
            if self.history_button.check_click(mouse_pos, single_click):
                self.state = MenuState.HISTORY
                self.history_scroll = 0
                return 'history'
            
            if self.exit_button.check_click(mouse_pos, single_click):
                return 'exit'
            
            self.draw_main_menu(game_time)
        
        elif self.state == MenuState.STORY:
            for event in events:
                if event.type == KEYDOWN and event.key == K_SPACE:
                    self.state = MenuState.NAME_INPUT
                    return 'name_input'
            
            self.draw_story(game_time)
        
        elif self.state == MenuState.NAME_INPUT:
            for event in events:
                self.name_input.handle_event(event)
            
            self.confirm_button.check_hover(mouse_pos)
            
            if self.name_input.text and self.confirm_button.check_click(mouse_pos, single_click):
                player_name = self.name_input.text or "Anonimo"
                self.history.start_session(player_name)
                self.name_input.text = ''
                return 'start_game'
            
            self.draw_name_input(game_time)
        
        elif self.state == MenuState.HISTORY:
            self.back_button.check_hover(mouse_pos)
            
            if self.back_button.check_click(mouse_pos, single_click):
                self.state = MenuState.MAIN
                return 'main'
            
            for event in events:
                if event.type == pygame.MOUSEWHEEL:
                    self.history_scroll = max(0, min(
                        len(self.history.history) - self.max_history_display,
                        self.history_scroll - event.y
                    ))
            
            self.draw_history()
        
        return None


# ============= SISTEMA DE NPCs =============
class NPC:
    def __init__(self, x, y, name, dialogues, npc_type='firewall'):
        self.pos = [x, y]
        self.name = name
        self.dialogues = dialogues
        self.current_dialogue = 0
        self.npc_type = npc_type
        self.interaction_radius = 20
        self.talked = False
    
    def can_interact(self, player_pos):
        distance = math.sqrt((self.pos[0] - player_pos[0])**2 + (self.pos[1] - player_pos[1])**2)
        return distance < self.interaction_radius
    
    def interact(self):
        if self.current_dialogue < len(self.dialogues):
            message = self.dialogues[self.current_dialogue]
            self.current_dialogue += 1
            self.talked = True
            return message
        return None
    
    def render(self, surface, scroll, game_time):
        screen_pos = [self.pos[0] - scroll[0], self.pos[1] - scroll[1]]
        
        if self.npc_type == 'firewall':
            size = 8
            glow = abs(math.sin(game_time * 0.05)) * 3
            pygame.draw.circle(surface, CYBER_COLORS['primary_cyan'], 
                             (int(screen_pos[0]), int(screen_pos[1])), int(size + glow), 2)
            pygame.draw.circle(surface, CYBER_COLORS['safe'], 
                             (int(screen_pos[0]), int(screen_pos[1])), int(size), 1)
            
            for i in range(4):
                angle = game_time * 0.02 + i * math.pi / 2
                x = screen_pos[0] + math.cos(angle) * (size - 2)
                y = screen_pos[1] + math.sin(angle) * (size - 2)
                pygame.draw.circle(surface, CYBER_COLORS['primary_green'], (int(x), int(y)), 2)
        
        elif self.npc_type == 'server':
            width, height = 16, 20
            pygame.draw.rect(surface, (40, 60, 100), 
                           (screen_pos[0] - width//2, screen_pos[1] - height//2, width, height))
            pygame.draw.rect(surface, CYBER_COLORS['primary_cyan'], 
                           (screen_pos[0] - width//2, screen_pos[1] - height//2, width, height), 2)
            
            for i in range(3):
                led_y = screen_pos[1] - 6 + i * 4
                led_color = CYBER_COLORS['safe'] if (game_time + i*10) % 30 < 15 else (0, 100, 0)
                pygame.draw.circle(surface, led_color, (int(screen_pos[0]), int(led_y)), 1)
        
        if not self.talked:
            indicator_y = screen_pos[1] - 15 + math.sin(game_time * 0.1) * 2
            pygame.draw.polygon(surface, CYBER_COLORS['warning'], [
                [screen_pos[0], indicator_y - 3],
                [screen_pos[0] - 3, indicator_y],
                [screen_pos[0] + 3, indicator_y]
            ])


# ============= SISTEMA DE PUZZLES =============
class CyberPuzzle:
    def __init__(self, x, y, puzzle_type, correct_answer, question):
        self.pos = [x, y]
        self.puzzle_type = puzzle_type
        self.correct_answer = correct_answer
        self.question = question
        self.active = False
        self.solved = False
        self.user_input = ""
        self.message = ""
        self.message_timer = 0
    
    def can_activate(self, player_pos):
        distance = math.sqrt((self.pos[0] - player_pos[0])**2 + (self.pos[1] - player_pos[1])**2)
        return distance < 25 and not self.solved
    
    def activate(self):
        self.active = True
        return self.question
    
    def check_answer(self, answer):
        if answer.upper().strip() == self.correct_answer.upper().strip():
            self.solved = True
            self.active = False
            self.message = "ACCESO CONCEDIDO!"
            self.message_timer = 120
            return True
        else:
            self.message = "ACCESO DENEGADO"
            self.message_timer = 60
            return False
    
    def update(self):
        if self.message_timer > 0:
            self.message_timer -= 1
    
    def render(self, surface, scroll, game_time):
        screen_pos = [self.pos[0] - scroll[0], self.pos[1] - scroll[1]]
        
        size = 12
        if not self.solved:
            color = CYBER_COLORS['warning']
            pulse = abs(math.sin(game_time * 0.1)) * 4
            
            pygame.draw.rect(surface, (60, 40, 0), 
                           (screen_pos[0] - size - pulse, screen_pos[1] - size - pulse, 
                            (size + pulse) * 2, (size + pulse) * 2))
            pygame.draw.rect(surface, color, 
                           (screen_pos[0] - size - pulse, screen_pos[1] - size - pulse, 
                            (size + pulse) * 2, (size + pulse) * 2), 2)
            
            pygame.draw.line(surface, color,
                           (screen_pos[0] - 6, screen_pos[1] - 6),
                           (screen_pos[0] + 6, screen_pos[1] + 6), 2)
            pygame.draw.line(surface, color,
                           (screen_pos[0] + 6, screen_pos[1] - 6),
                           (screen_pos[0] - 6, screen_pos[1] + 6), 2)
        else:
            color = CYBER_COLORS['safe']
            pygame.draw.rect(surface, (0, 60, 40), 
                           (screen_pos[0] - size, screen_pos[1] - size, size * 2, size * 2))
            pygame.draw.rect(surface, color, 
                           (screen_pos[0] - size, screen_pos[1] - size, size * 2, size * 2), 2)
            
            pygame.draw.line(surface, color,
                           (screen_pos[0] - 4, screen_pos[1]),
                           (screen_pos[0] - 1, screen_pos[1] + 4), 2)
            pygame.draw.line(surface, color,
                           (screen_pos[0] - 1, screen_pos[1] + 4),
                           (screen_pos[0] + 6, screen_pos[1] - 4), 2)


# ============= ESTRUCTURAS DE DATOS: QUEUE (COLA) =============
class PacketQueue:
    def __init__(self, max_size=10):
        self.queue = []
        self.max_size = max_size
        self.processed_count = 0
        self.threats_blocked = 0
    
    def enqueue(self, packet):
        if len(self.queue) < self.max_size:
            self.queue.append(packet)
            return True
        return False
    
    def dequeue(self):
        if not self.is_empty():
            return self.queue.pop(0)
        return None
    
    def peek(self):
        if not self.is_empty():
            return self.queue[0]
        return None
    
    def is_empty(self):
        return len(self.queue) == 0
    
    def is_full(self):
        return len(self.queue) >= self.max_size
    
    def size(self):
        return len(self.queue)
    
    def process_packet(self, is_threat):
        packet = self.dequeue()
        if packet:
            self.processed_count += 1
            if is_threat and packet['is_threat']:
                self.threats_blocked += 1
                return True
            elif not is_threat and not packet['is_threat']:
                return True
        return False


# ============= ESTRUCTURAS DE DATOS: STACK (PILA) =============
class FirewallRuleStack:
    def __init__(self, max_size=20):
        self.stack = []
        self.max_size = max_size
        self.message = ""
        self.message_timer = 0
        self.available_rules = ['BLOCK_IP', 'ALLOW_TCP', 'DENY_UDP', 'FILTER', 'INSPECT']
    
    def push(self, rule):
        if len(self.stack) < self.max_size:
            self.stack.append(rule)
            self.message = f'Regla {rule} agregada al Stack'
            self.message_timer = 60
            return True
        self.message = 'Stack lleno!'
        self.message_timer = 60
        return False
    
    def pop(self):
        if not self.is_empty():
            rule = self.stack.pop()
            self.message = f'UNDO: Regla {rule} removida'
            self.message_timer = 60
            return rule
        self.message = 'Stack vacio - sin reglas para deshacer'
        self.message_timer = 60
        return None
    
    def peek(self):
        if not self.is_empty():
            return self.stack[-1]
        return None
    
    def is_empty(self):
        return len(self.stack) == 0
    
    def size(self):
        return len(self.stack)
    
    def clear(self):
        self.stack = []
    
    def update(self, dt):
        if self.message_timer > 0:
            self.message_timer -= dt
    
    def render(self, surface, pos, game_time):
        panel_height = 12 + max(len(self.stack), 1) * 8 + 18
        pygame.draw.rect(surface, (10, 10, 20), 
                        (pos[0], pos[1], 75, panel_height))
        pygame.draw.rect(surface, CYBER_COLORS['primary_cyan'], 
                        (pos[0], pos[1], 75, panel_height), 1)
        
        font = text.Font('data/fonts/small_font.png', CYBER_COLORS['primary_green'])
        font.render('FIREWALL:', surface, (pos[0] + 2, pos[1] + 2))
        
        if self.is_empty():
            font.render('(Vacio)', surface, (pos[0] + 2, pos[1] + 12))
        else:
            for i, rule in enumerate(reversed(self.stack)):
                y_pos = pos[1] + 12 + i * 8
                is_top = (i == 0)
                color = CYBER_COLORS['warning'] if is_top and game_time % 40 < 20 else CYBER_COLORS['primary_cyan']
                font.render(rule[:10], surface, (pos[0] + 2, y_pos))
        
        help_y = pos[1] + panel_height - 16
        help_font = text.Font('data/fonts/small_font.png', CYBER_COLORS['primary_green'])
        help_font.render('[1-5]Add', surface, (pos[0] + 2, help_y))
        help_font.render('[U]Undo', surface, (pos[0] + 2, help_y + 8))
    
    def render_message(self, surface):
        if self.message_timer > 0:
            font = text.Font('data/fonts/small_font.png', CYBER_COLORS['primary_cyan'])
            msg_x = surface.get_width() // 2 - len(self.message) * 2
            msg_y = surface.get_height() - 30
            font.render(self.message, surface, (msg_x, msg_y))


# ============= SISTEMA IDS (INTRUSION DETECTION SYSTEM) =============
class IntrusionDetectionSystem:
    def __init__(self):
        self.threat_level = 0
        self.max_threat = 100
        self.alerts = []
        self.max_alerts = 5
        self.scan_timer = 0
        self.active_threats = []
    
    def update(self, dt):
        self.threat_level = max(0, self.threat_level - 0.1 * dt)
        self.scan_timer += dt
        
        if self.scan_timer >= 120:
            self.scan_timer = 0
        
        self.active_threats = [t for t in self.active_threats if t['timer'] > 0]
        for threat in self.active_threats:
            threat['timer'] -= dt
    
    def add_threat(self, threat_type, severity):
        self.threat_level = min(self.max_threat, self.threat_level + severity)
        self.active_threats.append({
            'type': threat_type,
            'severity': severity,
            'timer': 180,
            'color': CYBER_COLORS['danger'] if severity > 30 else CYBER_COLORS['warning']
        })
        
        alert_text = f"IDS: {threat_type} detectado!"
        if len(self.alerts) >= self.max_alerts:
            self.alerts.pop(0)
        self.alerts.append({'text': alert_text, 'timer': 120})
    
    def get_threat_color(self):
        if self.threat_level > 70:
            return CYBER_COLORS['danger']
        elif self.threat_level > 30:
            return CYBER_COLORS['warning']
        else:
            return CYBER_COLORS['safe']
    
    def render(self, surface, pos, game_time):
        bar_width = 60
        bar_height = 6
        
        pygame.draw.rect(surface, (20, 20, 20), (pos[0], pos[1], bar_width, bar_height))
        
        fill_width = int((self.threat_level / self.max_threat) * bar_width)
        pygame.draw.rect(surface, self.get_threat_color(), 
                        (pos[0], pos[1], fill_width, bar_height))
        pygame.draw.rect(surface, CYBER_COLORS['primary_cyan'], 
                        (pos[0], pos[1], bar_width, bar_height), 1)
        
        ids_font = text.Font('data/fonts/small_font.png', CYBER_COLORS['primary_cyan'])
        ids_font.render('IDS', surface, (pos[0], pos[1] - 8))
        
        y_offset = 0
        for alert in self.alerts:
            if alert['timer'] > 0:
                alert_font = text.Font('data/fonts/small_font.png', CYBER_COLORS['warning'])
                alert_font.render(alert['text'], surface, (pos[0], pos[1] + 10 + y_offset))
                alert['timer'] -= 1
                y_offset += 8


# ============= ANALIZADOR DE TRAFICO DE RED =============
class NetworkTrafficAnalyzer:
    def __init__(self):
        self.packets = []
        self.bandwidth_usage = 0
        self.max_bandwidth = 100
        self.packet_count = 0
        self.malicious_count = 0
    
    def add_packet(self, packet_type, is_malicious=False):
        self.packets.append({
            'type': packet_type,
            'pos': [0, random.randint(20, 180)],
            'speed': random.randint(1, 3),
            'is_malicious': is_malicious,
            'size': random.randint(2, 5)
        })
        self.packet_count += 1
        if is_malicious:
            self.malicious_count += 1
        
        self.bandwidth_usage = min(self.max_bandwidth, 
                                   len(self.packets) * 10)
    
    def update(self, dt):
        for packet in self.packets[:]:
            packet['pos'][0] += packet['speed'] * dt
            if packet['pos'][0] > 300:
                self.packets.remove(packet)
        
        self.bandwidth_usage = max(0, self.bandwidth_usage - 0.5 * dt)
    
    def render(self, surface, scroll, game_time):
        for packet in self.packets:
            screen_pos = [packet['pos'][0] - scroll[0], packet['pos'][1] - scroll[1]]
            color = CYBER_COLORS['danger'] if packet['is_malicious'] else CYBER_COLORS['primary_cyan']
            
            pulse = abs(math.sin(game_time * 0.1)) if packet['is_malicious'] else 1
            size = packet['size'] * pulse
            
            pygame.draw.circle(surface, color, (int(screen_pos[0]), int(screen_pos[1])), int(size))
            pygame.draw.circle(surface, (255, 255, 255), (int(screen_pos[0]), int(screen_pos[1])), int(size), 1)
    
    def get_stats(self):
        return {
            'total': self.packet_count,
            'malicious': self.malicious_count,
            'bandwidth': self.bandwidth_usage,
            'active': len(self.packets)
        }


# ============= MINI-JUEGO: FILTRO DE PAQUETES =============
class PacketFilteringGame:
    def __init__(self, x, y):
        self.pos = [x, y]
        self.packet_queue = PacketQueue(max_size=5)
        self.firewall_rules = FirewallRuleStack()
        self.active = False
        self.completed = False
        self.score = 0
        self.required_score = 10
        self.spawn_timer = 0
        self.interaction_radius = 30
    
    def can_activate(self, player_pos):
        distance = math.sqrt((self.pos[0] - player_pos[0])**2 + 
                            (self.pos[1] - player_pos[1])**2)
        return distance < self.interaction_radius and not self.completed
    
    def update(self, dt):
        if not self.active:
            return
        
        self.spawn_timer += dt
        if self.spawn_timer >= 60 and not self.packet_queue.is_full():
            is_threat = random.random() < 0.4
            packet = {
                'id': random.randint(1000, 9999),
                'is_threat': is_threat,
                'type': 'MALWARE' if is_threat else 'NORMAL',
                'timer': 300
            }
            self.packet_queue.enqueue(packet)
            self.spawn_timer = 0
    
    def process_current_packet(self, classify_as_threat):
        result = self.packet_queue.process_packet(classify_as_threat)
        if result:
            self.score += 1
            if self.score >= self.required_score:
                self.completed = True
                self.active = False
                return 'completed'
            return 'correct'
        else:
            self.score = max(0, self.score - 1)
            return 'incorrect'
    
    def render(self, surface, scroll, game_time):
        screen_pos = [self.pos[0] - scroll[0], self.pos[1] - scroll[1]]
        
        size = 15
        if not self.completed:
            color = CYBER_COLORS['primary_cyan']
            pulse = abs(math.sin(game_time * 0.08)) * 3
            
            pygame.draw.rect(surface, (0, 40, 60), 
                           (screen_pos[0] - size - pulse, screen_pos[1] - size - pulse,
                            (size + pulse) * 2, (size + pulse) * 2))
            pygame.draw.rect(surface, color, 
                           (screen_pos[0] - size - pulse, screen_pos[1] - size - pulse,
                            (size + pulse) * 2, (size + pulse) * 2), 2)
            
            for i in range(3):
                y = screen_pos[1] - 6 + i * 6
                pygame.draw.line(surface, color, 
                               (screen_pos[0] - 8, y), (screen_pos[0] + 8, y), 1)
        else:
            color = CYBER_COLORS['safe']
            pygame.draw.rect(surface, (0, 60, 40), 
                           (screen_pos[0] - size, screen_pos[1] - size, size * 2, size * 2))
            pygame.draw.rect(surface, color, 
                           (screen_pos[0] - size, screen_pos[1] - size, size * 2, size * 2), 2)
            
            pygame.draw.line(surface, color, 
                           (screen_pos[0] - 6, screen_pos[1]),
                           (screen_pos[0] - 2, screen_pos[1] + 6), 2)
            pygame.draw.line(surface, color,
                           (screen_pos[0] - 2, screen_pos[1] + 6),
                           (screen_pos[0] + 8, screen_pos[1] - 6), 2)
    
    def render_ui(self, surface):
        if not self.active:
            return
        
        ui_x = 20
        ui_y = 40
        
        title_font = text.Font('data/fonts/small_font.png', CYBER_COLORS['primary_cyan'])
        title_font.render('FILTRO DE PAQUETES', surface, (ui_x, ui_y))
        
        queue_y = ui_y + 15
        for i, packet in enumerate(self.packet_queue.queue):
            color = CYBER_COLORS['danger'] if packet['is_threat'] else CYBER_COLORS['safe']
            packet_font = text.Font('data/fonts/small_font.png', color)
            packet_text = f"{i+1}. {packet['type']}"
            packet_font.render(packet_text, surface, (ui_x, queue_y + i * 10))
        
        score_y = queue_y + len(self.packet_queue.queue) * 10 + 10
        score_font = text.Font('data/fonts/small_font.png', CYBER_COLORS['primary_green'])
        score_font.render(f"SCORE: {self.score}/{self.required_score}", surface, (ui_x, score_y))
        
        hint_font = text.Font('data/fonts/small_font.png', (150, 150, 150))
        hint_font.render("F: BLOQUEAR - G: PERMITIR", surface, (ui_x, score_y + 12))


# ============= FUNCIONES DE RENDERIZADO CYBER =============
def render_firewall(loc, size=[2, 3], color1=None, color2=None):
    global game_time
    if color1 is None:
        color1 = CYBER_COLORS['primary_green']
    if color2 is None:
        color2 = CYBER_COLORS['primary_cyan']
    
    points = []
    for i in range(6):
        angle = game_time / 30 + i / 6 * math.pi * 2
        radius = (math.sin((game_time * math.sqrt(i + 1)) / 20) * size[0] + size[1])
        x = loc[0] + math.cos(angle) * radius
        y = loc[1] + math.sin(angle) * radius
        points.append([x, y])
    
    pygame.draw.polygon(display, color1, points)
    pygame.draw.polygon(display, color2, points, 1)
    pygame.draw.circle(display, color2, (int(loc[0]), int(loc[1])), 2, 1)


def render_threat_warning(projectile, scroll, game_time):
    pos = [projectile[0][0] - scroll[0], projectile[0][1] - scroll[1]]
    
    size = 4
    warning_points = [
        [pos[0], pos[1] - size],
        [pos[0] - size, pos[1] + size],
        [pos[0] + size, pos[1] + size]
    ]
    
    threat_types = [
        CYBER_COLORS['danger'],
        CYBER_COLORS['warning'],
        (200, 0, 200),
        (255, 100, 0)
    ]
    color = threat_types[int(game_time / 30) % len(threat_types)]
    
    pygame.draw.polygon(display, color, warning_points)
    pygame.draw.polygon(display, (255, 255, 255), warning_points, 1)
    pygame.draw.circle(display, (255, 255, 255), (int(pos[0]), int(pos[1])), 1)


def render_server_boss(eye_base, scroll, eye_height, game_time):
    server_pos = [eye_base[0] - scroll[0], eye_base[1] - scroll[1]]
    
    server_width = 40
    server_height = int(eye_height * 1.5)
    
    server_rect = pygame.Rect(
        server_pos[0] - server_width // 2,
        server_pos[1] - server_height // 2,
        server_width,
        server_height
    )
    
    pygame.draw.rect(display, (50, 50, 80), server_rect)
    pygame.draw.rect(display, CYBER_COLORS['danger'], server_rect, 2)
    
    for i in range(4):
        if (game_time + i * 15) % 30 < 15:
            led_color = CYBER_COLORS['danger']
        else:
            led_color = (100, 0, 0)
        
        led_x = server_pos[0] - 15 + i * 10
        led_y = server_pos[1]
        pygame.draw.circle(display, led_color, (int(led_x), int(led_y)), 2)
    
    danger_x = server_pos[0]
    danger_y = server_pos[1] - 10
    pygame.draw.line(display, CYBER_COLORS['warning'], 
                    (danger_x - 5, danger_y - 5), 
                    (danger_x + 5, danger_y + 5), 2)
    pygame.draw.line(display, CYBER_COLORS['warning'], 
                    (danger_x + 5, danger_y - 5), 
                    (danger_x - 5, danger_y + 5), 2)


def render_secure_port(door_pos, scroll, game_time):
    pos = [door_pos[0] - scroll[0], door_pos[1] - scroll[1]]
    
    firewall_width = 12
    firewall_height = 18
    
    glow_intensity = abs(math.sin(game_time * 0.1))
    glow_color = (0, int(100 + glow_intensity * 155), 0)
    
    pygame.draw.rect(display, glow_color, 
                    (pos[0], pos[1], firewall_width, firewall_height))
    pygame.draw.rect(display, CYBER_COLORS['safe'], 
                    (pos[0], pos[1], firewall_width, firewall_height), 2)
    
    for i in range(3):
        y = pos[1] + i * 6
        pygame.draw.line(display, CYBER_COLORS['primary_cyan'], 
                        (pos[0], y), (pos[0] + firewall_width, y), 1)
    
    lock_x = pos[0] + firewall_width // 2
    lock_y = pos[1] + firewall_height // 2
    pygame.draw.circle(display, (255, 255, 255), (int(lock_x), int(lock_y)), 3, 1)
    pygame.draw.rect(display, (255, 255, 255), 
                    (lock_x - 2, lock_y, 4, 4), 1)


def render_cyber_hud(player_firewall, level_time):
    hud_color = CYBER_COLORS['primary_cyan']
    
    pygame.draw.line(display, hud_color, (0, 15), (display.get_width(), 15), 1)
    
    time_text = f"TIEMPO: {level_time // 60}s"
    time_font = text.Font('data/fonts/small_font.png', CYBER_COLORS['primary_green'])
    time_font.render(time_text, display, (display.get_width() - 80, 5))
    
    firewall_bar_width = 50
    firewall_bar_height = 6
    firewall_x = 10
    firewall_y = 20
    
    pygame.draw.rect(display, (30, 30, 30), 
                    (firewall_x, firewall_y, firewall_bar_width, firewall_bar_height))
    
    filled_width = int((player_firewall / 5) * firewall_bar_width)
    bar_color = CYBER_COLORS['safe'] if player_firewall > 2 else CYBER_COLORS['warning']
    pygame.draw.rect(display, bar_color, 
                    (firewall_x, firewall_y, filled_width, firewall_bar_height))
    
    pygame.draw.rect(display, hud_color, 
                    (firewall_x, firewall_y, firewall_bar_width, firewall_bar_height), 1)


# ============= JUEGO ORIGINAL CON TEMA CYBER =============
spritesheets, spritesheets_data = spritesheet_loader.load_spritesheets('data/images/tilesets/')
level_map = tile_map.TileMap((TILE_SIZE, TILE_SIZE), (300, 200))
level_name = 'level_1'

level_spawns = {
    'debug': [180, 50],
    'level_1': [180, 50],
    'level_2': [350, 80],
    'level_3': [350, 362],
    'level_4': [350, 202],
}

bounded = {
    'debug': False,
    'level_1': True,
    'level_2': True,
    'level_3': True,
    'level_4': False,
}

auto_return = {
    'debug': True,
    'level_1': True,
    'level_2': False,
    'level_3': False,
    'level_4': True,
}

# ============= DATOS DE NPCs Y PUZZLES =============
level_npcs = {
    'level_1': [
        NPC(250, 165, 'Firewall Alpha', [
            'Bienvenido, Guardian de Red.',
            'Los FIREWALLS bloquean trafico no autorizado.',
            'Recolecta recursos para explorar zonas peligrosas.'
        ], 'firewall'),
        NPC(450, 130, 'Servidor Aliado', [
            'Los ataques DDoS saturan servidores con trafico.',
            'Necesitas recursos para usar tu sonda remota.',
            'El puerto seguro esta al final del sector.'
        ], 'server'),
    ],
    'level_2': [
        NPC(450, 168, 'Firewall Beta', [
            'Este sector sufre ataques de paquetes maliciosos.',
            'Los atacantes envian datos daninos a la red.',
            'Usa tu agilidad para esquivar las amenazas.'
        ], 'firewall'),
        NPC(600, 168, 'Nodo de Inteligencia', [
            'El protocolo HTTPS protege las comunicaciones.',
            'Encripta datos entre cliente y servidor.',
            'Resuelve el terminal para avanzar de forma segura.'
        ], 'server'),
    ],
    'level_3': [
        NPC(400, 380, 'Firewall Gamma', [
            'Amenaza Persistente Avanzada (APT) detectada.',
            'Los APT son ataques sofisticados y prolongados.',
            'La ENCRIPTACION protege datos sensibles.'
        ], 'firewall'),
        NPC(550, 400, 'Centro de Operaciones', [
            'La encriptacion transforma datos en codigo.',
            'Solo quien tiene la clave puede leerlos.',
            'Es fundamental para la privacidad digital.'
        ], 'server'),
    ],
    'level_4': [
        NPC(400, 220, 'Firewall Omega', [
            'Has llegado al nucleo del sistema.',
            'La seguridad en capas usa multiples defensas.',
            'Felicidades, Guardian. Red restaurada!'
        ], 'firewall'),
    ],
}

level_puzzles = {
    'level_1': CyberPuzzle(
        650, 80, 'terminal',
        'FIREWALL',
        'Barrera que filtra trafico de red? (F_R_W_LL)'
    ),
    'level_2': CyberPuzzle(
        700, 120, 'terminal',
        'HTTPS',
        'Protocolo web seguro con encriptacion? (HTTP_)'
    ),
    'level_3': CyberPuzzle(
        650, 380, 'terminal',
        'ENCRYPTION',
        'Protege datos convirtiendolos en codigo? (_NCR_PT__N)'
    ),
    'level_4': CyberPuzzle(
        500, 220, 'terminal',
        'GUARDIAN',
        'Defensor de la seguridad digital? (GU_RD__N)'
    ),
}

# ============= MINI-JUEGOS DE FILTRADO DE PAQUETES POR NIVEL =============
level_packet_games = {
    'level_1': PacketFilteringGame(500, 165),
    'level_2': PacketFilteringGame(550, 100),
    'level_3': None,
    'level_4': None,
}

# Inicializar sistemas globales de ciberseguridad
ids_system = IntrusionDetectionSystem()
traffic_analyzer = NetworkTrafficAnalyzer()
firewall_stack = FirewallRuleStack()

# Load sounds with fallback for environments without audio
try:
    sounds = {k.split('.')[0]: pygame.mixer.Sound('data/sfx/' + k) for k in os.listdir('data/sfx')}
    sounds['eye_shoot'].set_volume(0.7)
    sounds['jump'].set_volume(0.3)
except:
    # Create empty sound dictionary if audio not available
    sounds = {k.split('.')[0]: None for k in os.listdir('data/sfx')}

def play_sound(sound_name):
    """Safely play a sound, handling cases where audio is not available"""
    if sound_name in sounds and sounds[sound_name] is not None:
        try:
            sounds[sound_name].play()
        except:
            pass

def play_music(music_file, loops=-1):
    """Safely play music, handling cases where audio is not available"""
    try:
        pygame.mixer.music.load(music_file)
        pygame.mixer.music.play(loops)
    except:
        pass

def fadeout_music(time_ms):
    """Safely fadeout music, handling cases where audio is not available"""
    try:
        pygame.mixer.music.fadeout(time_ms)
    except:
        pass

def reload_level(restart_audio=True):
    global player, projectiles, particles, scroll_target, events, soul_mode, level_time, player_mana, level_map, player_message, zoom, death, next_level, door, ready_to_exit, tutorial, tutorial_2, true_scroll, npcs, current_puzzle, puzzle_input_active, puzzle_user_input, current_packet_game, ids_system, traffic_analyzer, firewall_stack, show_level_objectives, objectives_dismissed
    level_map.load_map(level_name + '.json')
    player.pos = level_spawns[level_name].copy()
    soul.pos = level_spawns[level_name].copy()
    player.rotation = 0
    scroll_target = player.pos
    true_scroll = [player.center[0] - display.get_width() // 2, player.center[1] - display.get_height() // 2]
    zoom = 10
    events = {
        'lv1': 0,
        'lv1mana': 0,
        'lv1note': 0,
        'lv2timer': 0,
        'lv3timer': 0,
    }
    soul_mode = 0
    level_time = 0
    player_mana = 1
    death = 0
    next_level = False
    ready_to_exit = False
    player_message = [0, '', '']
    puzzle_input_active = False
    puzzle_user_input = ""
    show_level_objectives = True
    objectives_dismissed = False
    
    if level_name in level_npcs:
        npcs = [NPC(npc.pos[0], npc.pos[1], npc.name, npc.dialogues.copy(), npc.npc_type) 
                for npc in level_npcs[level_name]]
    else:
        npcs = []
    
    if level_name in level_puzzles:
        puzzle_data = level_puzzles[level_name]
        current_puzzle = CyberPuzzle(puzzle_data.pos[0], puzzle_data.pos[1], 
                                     puzzle_data.puzzle_type, puzzle_data.correct_answer, 
                                     puzzle_data.question)
    else:
        current_puzzle = None
    
    if level_name in level_packet_games and level_packet_games[level_name]:
        game_data = level_packet_games[level_name]
        current_packet_game = PacketFilteringGame(game_data.pos[0], game_data.pos[1])
    else:
        current_packet_game = None
    
    if level_name == 'level_1':
        tutorial = 0
        tutorial_2 = -1

    projectiles = []
    particles = []

    if level_name != 'level_1':
        door = None

    if restart_audio:
        if level_name == 'level_3':
            play_music('data/music_2.wav')
        else:
            play_music('data/music_1.wav')

def advance(pos, rot, amt):
    pos[0] += math.cos(rot) * amt
    pos[1] += math.sin(rot) * amt
    return pos

def particle_burst(loc, amt):
    global particles
    for i in range(amt):
        angle = random.randint(1, 360)
        speed = random.randint(20, 80) / 10
        vel = [math.cos(angle) * speed, math.sin(angle) * speed]
        particles.append(particles_m.Particle(loc[0], loc[1], 'light', vel, 0.8, 2 + random.randint(0, 20) / 10, custom_color=CYBER_COLORS['primary_cyan']))

animations = anim_loader.AnimationManager()

proj_img = pygame.image.load('data/images/projectile.png').convert()
proj_img.set_colorkey((0, 0, 0))
door_img = pygame.image.load('data/images/door.png').convert()
door_img.set_colorkey((0, 0, 0))

projectiles = []

particles_m.load_particle_images('data/images/particles')
particles = []

sparks = []

font = text.Font('data/fonts/small_font.png', CYBER_COLORS['primary_green'])
blue_font = text.Font('data/fonts/small_font.png', CYBER_COLORS['primary_cyan'])
red_font = text.Font('data/fonts/small_font.png', CYBER_COLORS['danger'])
black_font = text.Font('data/fonts/small_font.png', (0, 0, 1))

player = Entity(animations, level_spawns[level_name], (7, 13), 'player')
soul = Entity(animations, level_spawns[level_name], (7, 13), 'soul')
player_mana = 1
soul.offset = [-1, -1]
player_velocity = [0, 0]
air_timer = 0

true_scroll = [player.center[0] - display.get_width() // 2, player.center[1] - display.get_height() // 2]
scroll = true_scroll.copy()
scroll_target = player.pos
zoom = 1

left = False
right = False
up = False
down = False

game_time = 0
level_time = 0
death = 0
tutorial = 0
tutorial_2 = -1
events = {
    'lv1': 0,
    'lv1mana': 0,
    'lv1note': 0,
    'lv2timer': 0,
    'lv3timer': 0,
}
next_level = False

soul_mode = 0

player_message = [0, '', '']
player_bubble_size = 0
player_bubble_positions = [[0, 0], [0, 0], [0, 0]]

dt = 1
last_time = time.time()

door = (728, 60)
ready_to_exit = False

map_transition = 0

eye_target_height = 30
eye_height = 30

# Variables para NPCs y Puzzles
npcs = []
current_puzzle = None
puzzle_input_active = False
puzzle_user_input = ""

# Variables para mini-juego de filtrado de paquetes
current_packet_game = None

# Variables para objetivos de nivel
show_level_objectives = False
objectives_dismissed = False

# Inicializar menú
game_menu = GameMenu(display, font)
game_state = 'menu'
game_history = game_menu.history

play_music('data/music_1.wav')

# Función para renderizar objetivos del nivel
def render_level_objectives(current_level, game_time):
    if current_level not in LEVEL_OBJECTIVES:
        return
    
    obj_data = LEVEL_OBJECTIVES[current_level]
    
    # Fondo semi-transparente
    overlay = pygame.Surface((display.get_width(), display.get_height()))
    overlay.fill((5, 10, 15))
    overlay.set_alpha(230)
    display.blit(overlay, (0, 0))
    
    # Título del sector
    title_font = text.Font('data/fonts/small_font.png', CYBER_COLORS['primary_cyan'])
    title_x = display.get_width() // 2 - font.width(obj_data['title']) // 2
    title_font.render(obj_data['title'], display, (title_x, 20))
    
    pygame.draw.line(display, CYBER_COLORS['primary_cyan'], 
                    (20, 35), (display.get_width() - 20, 35), 1)
    
    # Objetivos
    y_offset = 45
    obj_label_font = text.Font('data/fonts/small_font.png', CYBER_COLORS['primary_green'])
    obj_label_font.render('OBJETIVOS:', display, (25, y_offset))
    y_offset += 15
    
    white_font = text.Font('data/fonts/small_font.png', (200, 200, 200))
    for objective in obj_data['objectives']:
        white_font.render(objective, display, (30, y_offset))
        y_offset += 11
    
    # Concepto educativo
    y_offset += 8
    pygame.draw.line(display, CYBER_COLORS['primary_cyan'], 
                    (20, y_offset), (display.get_width() - 20, y_offset), 1)
    y_offset += 8
    
    concept_lines = obj_data['concept'].split('\n')
    yellow_font = text.Font('data/fonts/small_font.png', (255, 220, 100))
    for line in concept_lines:
        yellow_font.render(line, display, (25, y_offset))
        y_offset += 10
    
    # Instrucción para continuar
    glow = abs(math.sin(game_time * 0.1)) * 20
    glow_color = (0, int(255 - glow), int(100 + glow))
    continue_font = text.Font('data/fonts/small_font.png', glow_color)
    continue_text = '[Presiona ESPACIO para iniciar]'
    continue_x = display.get_width() // 2 - font.width(continue_text) // 2
    continue_font.render(continue_text, display, (continue_x, display.get_height() - 20))

while True:
    # MENÚ
    if game_state == 'menu':
        current_events = pygame.event.get()
        for event in current_events:
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
        
        menu_result = game_menu.update(game_time, current_events, 
                                      pygame.mouse.get_pos(), 
                                      pygame.mouse.get_pressed()[0])
        
        if menu_result == 'start_game':
            game_state = 'playing'
            level_name = 'level_1'
            reload_level(True)
            pygame.mouse.set_visible(False)
        elif menu_result == 'exit':
            pygame.quit()
            sys.exit()
        
        screen.blit(pygame.transform.scale(display, screen.get_size()), (0, 0))
        pygame.display.update()
        clock.tick(60)
        game_time += 1
        continue
    
    # JUEGO
    display.fill(CYBER_COLORS['bg_dark'])

    game_time += 1
    level_time += 1
    if death:
        death += 1
        if death > 70:
            if map_transition == 0:
                map_transition = 1

    if map_transition:
        last = map_transition
        map_transition += dt
        if (last < 60) and (map_transition >= 60):
            if next_level:
                level_n = int(level_name.split('_')[-1])
                level_name = level_name.split('_')[0] + '_' + str(level_n + 1)
                game_history.add_level_completed(level_name)
            reload_level(next_level)
        if map_transition > 120:
            map_transition = 0

    # background con grid cyber
    grid_color = (0, 50, 80)
    for x in range(0, display.get_width(), 20):
        if abs(math.sin(game_time * 0.01 + x * 0.1)) > 0.5:
            pygame.draw.line(display, grid_color, (x, 0), (x, display.get_height()), 1)
    
    for y in range(0, display.get_height(), 20):
        if abs(math.sin(game_time * 0.01 + y * 0.1)) > 0.5:
            pygame.draw.line(display, grid_color, (0, y), (display.get_width(), y), 1)

    b_points = [[0, 16]]
    b_points += [[display.get_width() / 30 * (i + 1) + math.sin((game_time + i * 120) / 4) * 8, 16 + math.sin((game_time + i * 10) / 10) * 4] for i in range(29)]
    b_points += [[display.get_width(), 16], [display.get_width(), 0], [0, 0]]
    b2_points = [[0, 16]]
    b2_points += [[display.get_width() / 30 * (i + 1) + math.sin((game_time + i * 120 - scroll[0] * 0.5) / 10) * 8, 16 + math.sin((game_time + i * 10) / 10) * 4] for i in range(29)]
    b2_points += [[display.get_width(), 16], [display.get_width(), 0], [0, 0]]
    b2_points = [[display.get_width() - p[0], p[1] * 3] for p in b2_points]
    back_surf = pygame.Surface((display.get_width(), 72))
    pygame.draw.polygon(back_surf, (10, 15, 30), b2_points)
    back_surf.set_colorkey((0, 0, 0))
    display.blit(back_surf, (0, 0))
    display.blit(pygame.transform.flip(back_surf, False, True), (0, display.get_height() - 72))

    # camera
    if (not map_transition) or (map_transition > 60):
        zoom += (1 - zoom) / 7
        if abs(1 - zoom) < 0.005:
            zoom = 1
    else:
        zoom += (5 - zoom) / 50

    if abs(int(scroll_target[0]) - display.get_width() // 2 - 3 - true_scroll[0]) < 0.5:
        true_scroll[0] = int(scroll_target[0]) - display.get_width() // 2 - 3
    else:
        true_scroll[0] += (int(scroll_target[0]) - display.get_width() // 2 - 3 - true_scroll[0]) / 20 * dt
    if abs(scroll_target[1] - display.get_height() // 2 - 5 - true_scroll[1]) <= 1:
        true_scroll[1] = int(scroll_target[1]) - display.get_height() // 2 - 5
    else:
        true_scroll[1] += (scroll_target[1] - display.get_height() // 2 - 5 - true_scroll[1]) / 20 * dt
    scroll = [int(true_scroll[0]), int(true_scroll[1])]
    if bounded[level_name]:
        size = [int(display.get_width() / zoom), int(display.get_height() / zoom)]
        zoom_offset = [(display.get_width() - size[0]) // 2, (display.get_height() - size[1]) // 2]
        scroll[0] = max(level_map.left * TILE_SIZE + TILE_SIZE * 3 - zoom_offset[0], min(level_map.right * TILE_SIZE - display.get_width() - TILE_SIZE * 2 + zoom_offset[0], scroll[0]))
        scroll[1] = max(level_map.top * TILE_SIZE + TILE_SIZE * 3 - zoom_offset[1], min(level_map.bottom * TILE_SIZE - display.get_height() - TILE_SIZE * 4 + zoom_offset[1], scroll[1]))

    # door - ahora es puerto seguro
    if door:
        puzzle_solved = (not current_puzzle) or current_puzzle.solved
        
        if puzzle_solved:
            render_secure_port(door, scroll, game_time)
        else:
            pos = [door[0] - scroll[0], door[1] - scroll[1]]
            pygame.draw.rect(display, (60, 20, 20), (pos[0], pos[1], 12, 18))
            pygame.draw.rect(display, CYBER_COLORS['danger'], (pos[0], pos[1], 12, 18), 2)
            if game_time % 60 < 30:
                font.render('BLOQUEADO', display, (pos[0] - 20, pos[1] - 15))
        
        if random.randint(1, 7) == 1:
            color = CYBER_COLORS['safe'] if puzzle_solved else CYBER_COLORS['danger']
            particles.append(particles_m.Particle(door[0] + 6, door[1] + 9, 'light', [random.randint(0, 10) / 10 - 0.5, random.randint(0, 10) / 10 - 2], 0.1, 3.5 + random.randint(0, 20) / 10, custom_color=color))
        
        if player.get_distance([door[0] + 6, door[1] + 9]) < 5:
            if puzzle_solved:
                if map_transition == 0:
                    fadeout_music(500)
                    map_transition = 1
                    next_level = True
                    play_sound('door')
            else:
                if player_message[0] == 0:
                    player_message = [120, 'Terminal de acceso bloqueada!', '']

    # render tiles
    render_list = level_map.get_visible(scroll)
    collideables = []
    for layer in render_list:
        for tile in layer:
            offset = [0, 0]
            if tile[1][0] in spritesheets_data:
                tile_id = str(tile[1][1]) + ';' + str(tile[1][2])
                if tile_id in spritesheets_data[tile[1][0]]:
                    if 'tile_offset' in spritesheets_data[tile[1][0]][tile_id]:
                        offset = spritesheets_data[tile[1][0]][tile_id]['tile_offset']
            if tile[1][0] == 'ground':
                collideables.append(pygame.Rect(tile[0][0], tile[0][1], TILE_SIZE, TILE_SIZE))
            if tile[1][0] == 'torches':
                if random.randint(1, 6) == 1:
                    particles.append(particles_m.Particle(tile[0][0] + 6, tile[0][1] + 4, 'light', [random.randint(0, 10) / 10 - 0.5, random.randint(0, 10) / 10 - 2], 0.1, 3 + random.randint(0, 20) / 10, custom_color=CYBER_COLORS['primary_cyan']))
                torch_sin = math.sin((tile[0][1] % 100 + 200) / 300 * game_time * 0.01)
                particles_m.blit_center_add(display, particles_m.circle_surf(15 + (torch_sin + 3) * 8.5, (0, 4 + (torch_sin + 4) * 0.5, 8 + (torch_sin + 4) * 0.9)), (tile[0][0] - scroll[0] + 6, tile[0][1] - scroll[1] + 4))
                particles_m.blit_center_add(display, particles_m.circle_surf(9 + (torch_sin + 3) * 4, (0, 8 + (torch_sin + 4) * 0.5, 12 + (torch_sin + 4) * 0.9)), (tile[0][0] - scroll[0] + 6, tile[0][1] - scroll[1] + 4))
            if (tile[1][0] == 'decorations') and (tile[1][1] == 0):
                if random.randint(1, 2) == 1:
                    p_offset = random.choice([[-8, 1], [8, 1], [4, 4], [-4, 4]])
                    particles.append(particles_m.Particle(tile[0][0] + TILE_SIZE + p_offset[0], tile[0][1] + TILE_SIZE * 1.5 + p_offset[1], 'light', [random.randint(0, 10) / 10 - 0.5, random.randint(0, 10) / 10 - 2], 0.1, 4 + random.randint(0, 20) / 10, custom_color=CYBER_COLORS['primary_cyan']))
                torch_sin = math.sin((tile[0][1] % 100 + 200) / 300 * game_time * 0.01)
                particles_m.blit_center_add(display, particles_m.circle_surf(15 + (torch_sin + 3) * 8.5, (0, 4 + (torch_sin + 4) * 0.7, 8 + (torch_sin + 4) * 1.3)), (tile[0][0] - scroll[0] + TILE_SIZE, tile[0][1] - scroll[1] + TILE_SIZE * 1.5))
                particles_m.blit_center_add(display, particles_m.circle_surf(9 + (torch_sin + 3) * 4, (0, 8 + (torch_sin + 4) * 0.7, 12 + (torch_sin + 4) * 1.3)), (tile[0][0] - scroll[0] + TILE_SIZE, tile[0][1] - scroll[1]  + TILE_SIZE * 1.5))
            if tile[1][0] != 'mana':
                img = spritesheet_loader.get_img(spritesheets, tile[1])
                display.blit(img, (math.floor(tile[0][0] - scroll[0] + offset[0]), math.floor(tile[0][1] - scroll[1] + offset[1])))
            else:
                render_firewall([tile[0][0] + 6 - scroll[0], tile[0][1] + 6 - scroll[1]])
                torch_sin = math.sin((tile[0][1] % 100 + 200) / 300 * game_time * 0.01)
                particles_m.blit_center_add(display, particles_m.circle_surf(15 + (torch_sin + 3) * 8.5, (0, 4 + (torch_sin + 4) * 0.5, 8 + (torch_sin + 4) * 0.9)), (tile[0][0] - scroll[0] + 6, tile[0][1] - scroll[1] + 4))
                particles_m.blit_center_add(display, particles_m.circle_surf(9 + (torch_sin + 3) * 4, (0, 8 + (torch_sin + 4) * 0.5, 12 + (torch_sin + 4) * 0.9)), (tile[0][0] - scroll[0] + 6, tile[0][1] - scroll[1] + 4))
    
    # Renderizar NPCs y Puzzles
    for npc in npcs:
        npc.render(display, scroll, game_time)
        if npc.can_interact(player.pos) and not npc.talked:
            screen_pos = [npc.pos[0] - scroll[0], npc.pos[1] - scroll[1]]
            font.render('[E]', display, (screen_pos[0] - 8, screen_pos[1] - 25))
    
    if current_puzzle:
        current_puzzle.update()
        current_puzzle.render(display, scroll, game_time)
        if current_puzzle.can_activate(player.pos) and not current_puzzle.solved:
            screen_pos = [current_puzzle.pos[0] - scroll[0], current_puzzle.pos[1] - scroll[1]]
            font.render('[E] Acceder', display, (screen_pos[0] - 20, screen_pos[1] - 25))
        
        if current_puzzle.message_timer > 0:
            msg_y = display.get_height() // 2 + 40
            if current_puzzle.solved:
                blue_font.render(current_puzzle.message, display, 
                               (display.get_width() // 2 - font.width(current_puzzle.message) // 2, msg_y))
            else:
                red_font.render(current_puzzle.message, display,
                              (display.get_width() // 2 - font.width(current_puzzle.message) // 2, msg_y))
    
    if current_packet_game:
        current_packet_game.update(dt)
        current_packet_game.render(display, scroll, game_time)
        if current_packet_game.can_activate(player.pos) and not current_packet_game.completed:
            screen_pos = [current_packet_game.pos[0] - scroll[0], current_packet_game.pos[1] - scroll[1]]
            font.render('[E] Filtrado', display, (screen_pos[0] - 20, screen_pos[1] - 25))
        current_packet_game.render_ui(display)
    
    ids_system.update(dt)
    ids_system.render(display, [display.get_width() - 70, 30], game_time)
    
    firewall_stack.update(dt)
    firewall_stack.render(display, [10, 30], game_time)
    firewall_stack.render_message(display)
    
    if game_time % 120 == 0 and random.random() < 0.3:
        is_mal = random.random() < 0.4
        traffic_analyzer.add_packet('TCP', is_mal)
        if is_mal:
            ids_system.add_threat('Trafico Malicioso', random.randint(10, 40))
    
    traffic_analyzer.update(dt)
    if level_name in ['level_2', 'level_3']:
        traffic_analyzer.render(display, scroll, game_time)
    
    # Renderizar jugador después de tiles pero antes de actualización
    if not death:
        player.render(display, scroll)

    # player
    player.update(1 / 60 * dt)
    air_timer += 1

    if not map_transition:
        player_velocity[1] = min(player_velocity[1] + 0.23 * dt, 5)
    movement = player_velocity.copy()
    if not death and not soul_mode and not map_transition:
        if right:
            movement[0] += 1.5
        if left:
            movement[0] -= 1.5
    if death:
        collideables = []
        movement[0] = 1
        player.rotation -= 10
    if death == 2:
        player_velocity[1] = -7
        game_history.add_breach()
    movement[0] *= min(dt, 3)
    movement[1] *= dt
    movement[1] = min(8, movement[1])
    if not map_transition:
        collisions = player.move(movement, collideables)
    else:
        collisions = {'top': False, 'bottom': False, 'left': False, 'right': False}
    if collisions['top'] or collisions['bottom']:
        player_velocity[1] = 0
    if collisions['bottom']:
        air_timer = 0

    if air_timer > 3:
        player.set_action('jump')
    elif movement[0] != 0:
        player.set_action('run')
    else:
        player.set_action('idle')
        if soul_mode:
            player.set_action('idle', True)

    if movement[0] > 0:
        player.flip[0] = False
    if movement[0] < 0:
        player.flip[0] = True

    if soul_mode:
        player.opacity = 120
        movement = [0, 0]
        if right:
            movement[0] += 0.75 * dt
        if left:
            movement[0] -= 0.75 * dt
        if up:
            movement[1] -= 0.75 * dt
        if down:
            movement[1] += 0.75 * dt
        soul_mode += max(dt, 0.3)
        if auto_return[level_name]:
            if soul_mode > 240:
                soul_mode = 0
                play_sound('exit_soul')
                particle_burst(player.center, 50)
                player.pos = soul.pos.copy()
                particle_burst(player.center, 50)
                scroll_target = player.pos
                player_velocity[1] = 0
        soul.move(movement, collideables)
        if soul.pos[0] < scroll[0]:
            soul.pos[0] = scroll[0]
        if soul.pos[0] > scroll[0] + display.get_width():
            soul.pos[0] = scroll[0] + display.get_width()
        if soul.pos[1] < scroll[1]:
            soul.pos[1] = scroll[1]
        if soul.pos[1] > scroll[1] + display.get_height():
            soul.pos[1] = scroll[1] + display.get_height()
        if random.randint(1, 3) == 1:
            particles.append(particles_m.Particle(soul.pos[0] + 3, soul.pos[1] + 4, 'light', [random.randint(0, 10) / 10 - 0.5, random.randint(0, 10) / 10 + 1], 0.2, 3 + random.randint(0, 20) / 10, custom_color=CYBER_COLORS['primary_cyan']))
        torch_sin = math.sin((soul.center[1] % 100 + 200) / 300 * game_time * 0.1)
        particles_m.blit_center_add(display, particles_m.circle_surf(7 + (torch_sin + 3) * 3, (0, 4 + (torch_sin + 4) * 0.5, 18 + (torch_sin + 4) * 0.9)), (soul.center[0] - 1 - scroll[0], soul.center[1] - 4 - scroll[1]))
        particles_m.blit_center_add(display, particles_m.circle_surf(5 + (torch_sin + 3) * 2, (0, 8 + (torch_sin + 4) * 0.5, 18 + (torch_sin + 4) * 0.9)), (soul.center[0] - 1 - scroll[0], soul.center[1] - 4 - scroll[1]))
        if tutorial_2 == 0:
            tutorial_2 = 1
    else:
        player.opacity = 255

    if level_map.tile_collide(player.center):
        tile = level_map.tile_collide(player.center)
        tile_center = [player.center[0] // TILE_SIZE * TILE_SIZE + TILE_SIZE // 2, player.center[1] // TILE_SIZE * TILE_SIZE + TILE_SIZE // 2]
        rm = None
        for layer in tile:
            if tile[layer][0] == 'mana':
                play_sound('mana_1')
                play_sound('mana_2')
                player_mana += 1
                game_history.add_firewall_collected()
                rm = layer
                for i in range(2):
                    sparks.append([tile_center.copy(), math.pi / 2 + math.pi * i, 10, 6, CYBER_COLORS['primary_green']])
                    sparks.append([tile_center.copy(), math.pi * i, 6, 3, CYBER_COLORS['primary_cyan']])
                for i in range(20):
                    particles.append(particles_m.Particle(tile_center[0], tile_center[1], 'light', [random.randint(0, 10) / 10 - 0.5, (random.randint(0, 120) / 10 + 1) * random.choice([-1, 1])], 0.1, 2 + random.randint(0, 20) / 10, custom_color=CYBER_COLORS['primary_green']))
        if rm:
            del tile[rm]

    # input
    for event in pygame.event.get():
        if event.type == QUIT:
            if game_state == 'playing':
                game_history.end_session(level_name)
            pygame.quit()
            sys.exit()
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                if game_state == 'playing':
                    game_history.end_session(level_name)
                    game_state = 'menu'
                    game_menu.state = MenuState.MAIN
                    pygame.mouse.set_visible(True)
                else:
                    pygame.quit()
                    sys.exit()
            
            if event.key == K_SPACE and show_level_objectives and not objectives_dismissed:
                show_level_objectives = False
                objectives_dismissed = True
            
            if puzzle_input_active:
                if event.key == K_BACKSPACE:
                    puzzle_user_input = puzzle_user_input[:-1]
                elif event.key == K_RETURN:
                    if current_puzzle and puzzle_user_input:
                        if current_puzzle.check_answer(puzzle_user_input):
                            play_sound('mana_1')
                            player_message = [180, 'Terminal desbloqueada!', '']
                        else:
                            play_sound('death')
                            player_message = [180, 'Acceso denegado. Intenta de nuevo.', '']
                        puzzle_user_input = ""
                        puzzle_input_active = False
                elif event.key == K_ESCAPE:
                    puzzle_input_active = False
                    puzzle_user_input = ""
                elif len(puzzle_user_input) < 20:
                    if event.unicode.isalnum() or event.unicode == ' ':
                        puzzle_user_input += event.unicode.upper()
            
            if event.key == K_e and not puzzle_input_active:
                for npc in npcs:
                    if npc.can_interact(player.pos):
                        message = npc.interact()
                        if message:
                            player_message = [300, message, '']
                            play_sound('thought')
                        break
                
                if current_puzzle and not current_puzzle.solved:
                    if current_puzzle.can_activate(player.pos):
                        puzzle_input_active = True
                        puzzle_user_input = ""
                        player_message = [400, current_puzzle.question, '']
                        play_sound('thought')
                
                if current_packet_game and current_packet_game.can_activate(player.pos):
                    current_packet_game.active = not current_packet_game.active
                    if current_packet_game.active:
                        player_message = [300, 'Mini-juego: Filtrado de Paquetes activado!', '']
                        play_sound('thought')
            
            if event.key == K_f and current_packet_game and current_packet_game.active:
                result = current_packet_game.process_current_packet(True)
                if result == 'completed':
                    player_message = [200, 'Sistema de filtrado completado!', '']
                    player_mana += 1
                    play_sound('mana_1')
                elif result == 'correct':
                    play_sound('mana_2')
                else:
                    play_sound('death')
            
            if event.key == K_g and current_packet_game and current_packet_game.active:
                result = current_packet_game.process_current_packet(False)
                if result == 'completed':
                    player_message = [200, 'Sistema de filtrado completado!', '']
                    player_mana += 1
                    play_sound('mana_1')
                elif result == 'correct':
                    play_sound('mana_2')
                else:
                    play_sound('death')
            
            if event.key == K_1:
                if firewall_stack.push(firewall_stack.available_rules[0]):
                    play_sound('mana_2')
            if event.key == K_2:
                if firewall_stack.push(firewall_stack.available_rules[1]):
                    play_sound('mana_2')
            if event.key == K_3:
                if firewall_stack.push(firewall_stack.available_rules[2]):
                    play_sound('mana_2')
            if event.key == K_4:
                if firewall_stack.push(firewall_stack.available_rules[3]):
                    play_sound('mana_2')
            if event.key == K_5:
                if firewall_stack.push(firewall_stack.available_rules[4]):
                    play_sound('mana_2')
            if event.key == K_u:
                if firewall_stack.pop():
                    play_sound('death')
            
            if event.key == K_q:
                player_message = [180, 'Test message', '']
            if event.key == K_RIGHT:
                right = True
                if not tutorial:
                    tutorial = 1
            if event.key == K_LEFT:
                left = True
            if event.key == K_DOWN:
                if not ready_to_exit:
                    if (level_name != 'level_1') or (events['lv1'] != 0) and (not map_transition):
                        if soul_mode == 0:
                            if player_mana > 0:
                                soul_mode = 1
                                play_sound('enter_soul')
                                soul.pos = player.pos.copy()
                                player.pos = player.pos.copy()
                                particle_burst(player.center, 50)
                                player_mana -= 1
                            else:
                                player_message = [200, CYBER_MESSAGES['need_firewall'], '']
                else:
                    player_message = [300, CYBER_MESSAGES['move_on'], '']
                down = True
            if event.key == K_UP:
                if not death and (air_timer < 5) and not soul_mode and not map_transition:
                    play_sound('jump')
                    player_velocity[1] = -5.2
                    sparks.append([list(player.rect.bottomleft), math.pi * 0.9, 2 + random.randint(0, 10) / 10, 5, CYBER_COLORS['primary_cyan']])
                    sparks.append([list(player.rect.bottomright), math.pi * 0.1, 2 + random.randint(0, 10) / 10, 5, CYBER_COLORS['primary_cyan']])
                up = True
        if event.type == KEYUP:
            if event.key == K_RIGHT:
                right = False
            if event.key == K_LEFT:
                left = False
            if event.key == K_DOWN:
                down = False
            if event.key == K_UP:
                up = False

    if death:
        player.render(display, scroll)

    # servidor infectado (reemplaza el ojo)
    eye_base = [386, 220]
    if not soul_mode:
        eye_angle = player.get_angle(eye_base) + math.pi
    else:
        eye_angle = soul.get_angle(eye_base) + math.pi
    if level_name == 'level_3':
        if (6200 < events['lv3timer'] < 6600):
            eye_base = [386 + random.randint(0, 8) - 4, 220 + random.randint(0, 8) - 4]
            eye_target_height = 24
        if random.randint(0, 180) == 0:
            eye_height = 2
        eye_height += (eye_target_height - eye_height) / 20
        if events['lv3timer'] < 6800:
            render_server_boss(eye_base, scroll, eye_height, game_time)

    # events
    dt = (time.time() - last_time) * 60
    last_time = time.time()

    reset = False
    if level_name == 'level_1':
        if not events['lv1note'] and player_mana:
            if events['lv1mana'] and (player_bubble_size < 0.05) and (player_message[0] == 0) and (level_time > 1500):
                player_message = [320, CYBER_MESSAGES['exit_up'], '']
                events['lv1note'] = 1
        if (events['lv1note'] == 1) and player_mana:
            if events['lv1mana'] and (player_bubble_size < 0.05) and (player_message[0] == 0) and (level_time > 2500):
                player_message = [500, CYBER_MESSAGES['remote_scan'], '']
                events['lv1note'] = 2
        if not events['lv1mana']:
            if player.pos[0] > 530:
                player_message = [320, CYBER_MESSAGES['need_firewall'], '']
                events['lv1mana'] = 1

        if not events['lv1']:
            if player.pos[0] > 446:
                events['lv1'] = 1
                for i in range(17):
                    vel = [-4, 0]
                    angle = math.atan2(vel[1], vel[0])
                    spawn = [display.get_width() + scroll[0], display.get_height() * i / 15 + scroll[1]]
                    for j in range(5):
                        sparks.append([spawn.copy(), angle + math.radians(random.randint(0, 80) - 40), 4 + random.randint(0, 30) / 10, 10, CYBER_COLORS['danger']])
                    projectiles.append([spawn, vel, 'enemy'])
                play_sound('eye_shoot_large')
        if events['lv1']:
            if events['lv1'] != -1:
                events['lv1'] += dt
                if events['lv1'] > 33:
                    if not soul_mode:
                        dt = 0
                    else:
                        dt = 0.5
                    if tutorial_2 == -1:
                        tutorial_2 = 0
                if soul_mode > 20:
                    events['lv1'] = -1

    if level_name == 'level_2':
        last = events['lv2timer']
        events['lv2timer'] += dt
        if events['lv2timer'] < 6:
            player_message = [420, 'Preparate para el desafio...', '']
        if (last < 920) and (events['lv2timer'] >= 920):
            reset = True
            player_message = [420, 'Esquiva los paquetes maliciosos!', '']
        if (last < 1840) and (events['lv2timer'] >= 1840):
            reset = True
        if (last < 2750) and (events['lv2timer'] >= 2750):
            reset = True
        if (3200 < events['lv2timer'] < 3500):
            if (events['lv2timer'] % 350 < last % 350) or (events['lv2timer'] % 180 < last % 180):
                dir = random.choice([-1, 1])
                offset = random.randint(0, 20) / 20
                for i in range(6):
                    i -= offset
                    vel = [3.5 * dir, 0]
                    angle = math.atan2(vel[1], vel[0])
                    if dir == -1:
                        spawn = [display.get_width() + scroll[0], display.get_height() * i / 5 + scroll[1]]
                    else:
                        spawn = [scroll[0], display.get_height() * i / 5 + scroll[1]]
                    for j in range(5):
                        sparks.append([spawn.copy(), angle + math.radians(random.randint(0, 80) - 40), 4 + random.randint(0, 30) / 10, 10, CYBER_COLORS['danger']])
                    projectiles.append([spawn, vel, 'enemy'])
                play_sound('eye_shoot_large')
        if (last < 3700) and (events['lv2timer'] >= 3700):
            reset = True
            player_message = [420, CYBER_MESSAGES['clear'], '']
            door = (330, 372)
            ready_to_exit = True
            play_sound('end_level')
    
    if level_name == 'level_3':
        last = events['lv3timer']
        events['lv3timer'] += dt
        if events['lv3timer'] < 6:
            player_message = [200, CYBER_MESSAGES['threat'], '']
        if (200 < events['lv3timer'] < 800):
            eye_target_height = 30
            if random.randint(0, 70) == 0:
                play_sound('eye_shoot_large')
                for i in range(5):
                    speed = random.randint(30, 40) / 10
                    angle = eye_angle + random.random() * math.pi / 4 - math.pi / 8
                    vel = [math.cos(angle) * speed, math.sin(angle) * speed]
                    spawn = eye_base.copy()
                    for j in range(3):
                        sparks.append([spawn.copy(), angle + math.radians(random.randint(0, 80) - 40), 4 + random.randint(0, 30) / 10, 10, CYBER_COLORS['danger']])
                    projectiles.append([spawn, vel, 'enemy'])
        elif (1300 < events['lv3timer'] < 1800):
            eye_target_height = 30
            if random.randint(0, 90) == 0:
                play_sound('eye_shoot_large')
                offset = random.random() * math.pi * 2
                for i in range(36):
                    speed = 3.5
                    angle = math.pi * 2 * i / 36 + offset
                    vel = [math.cos(angle) * speed, math.sin(angle) * speed]
                    spawn = eye_base.copy()
                    for j in range(3):
                        sparks.append([spawn.copy(), angle + math.radians(random.randint(0, 80) - 40), 4 + random.randint(0, 30) / 10, 10, CYBER_COLORS['danger']])
                    projectiles.append([spawn, vel, 'enemy'])
        elif (2500 < events['lv3timer'] < 3100):
            eye_target_height = 38
            if game_time % 10 == 0:
                play_sound('eye_shoot')
                offset = game_time / 600 * math.pi * 2
                for i in range(6):
                    speed = 3.5
                    angle = math.pi * 2 * i / 6 + offset
                    vel = [math.cos(angle) * speed, math.sin(angle) * speed]
                    spawn = eye_base.copy()
                    for j in range(3):
                        sparks.append([spawn.copy(), angle + math.radians(random.randint(0, 80) - 40), 7 + random.randint(0, 30) / 10, 5, CYBER_COLORS['danger']])
                    projectiles.append([spawn, vel, 'enemy'])
        elif (3600 < events['lv3timer'] < 4500):
            eye_target_height = 38
            if game_time % 17 == 0:
                play_sound('eye_shoot')
                for j in range(2):
                    if j == 0:
                        offset = game_time / 600 * math.pi * 2
                    else:
                        offset = -game_time / 600 * math.pi * 2
                    for i in range(6):
                        speed = 3.5
                        angle = math.pi * 2 * i / 6 + offset
                        vel = [math.cos(angle) * speed, math.sin(angle) * speed]
                        spawn = eye_base.copy()
                        for k in range(3):
                            sparks.append([spawn.copy(), angle + math.radians(random.randint(0, 80) - 40), 7 + random.randint(0, 30) / 10, 5, CYBER_COLORS['danger']])
                        projectiles.append([spawn, vel, 'enemy'])
        elif (5200 < events['lv3timer'] < 5800):
            eye_target_height = 30
            if game_time % 3 == 0:
                play_sound('eye_shoot')
                offset = game_time / 600 * math.pi * 2
                for i in range(3):
                    speed = 3.5
                    angle = math.pi * 2 * i / 3 + offset
                    vel = [math.cos(angle) * speed, math.sin(angle) * speed]
                    spawn = eye_base.copy()
                    for j in range(3):
                        sparks.append([spawn.copy(), angle + math.radians(random.randint(0, 80) - 40), 7 + random.randint(0, 30) / 10, 5, CYBER_COLORS['danger']])
                    projectiles.append([spawn, vel, 'enemy'])
        else:
            eye_target_height = 4
        if (last < 1150) and (events['lv3timer'] >= 1150):
            reset = True
        if (last < 2300) and (events['lv3timer'] >= 2300):
            reset = True
        if (last < 3400) and (events['lv3timer'] >= 3400):
            reset = True
        if (last < 4800) and (events['lv3timer'] >= 4800):
            reset = True
        if (last < 6200) and (events['lv3timer'] >= 6200):
            play_sound('shake')
        if (last < 6800) and (events['lv3timer'] >= 6800):
            reset = True
            player_message = [200, CYBER_MESSAGES['silence'], '']
            door = (360, 360)
            play_sound('end_level')
            play_sound('death')
            ready_to_exit = True
            for i in range(35):
                sparks.append([eye_base.copy(), math.radians(random.randint(1, 360)), 7 + random.randint(0, 30) / 10, 8, CYBER_COLORS['primary_green']])
            for i in range(300):
                angle = random.randint(1, 360)
                speed = random.randint(70, 250) / 10
                vel = [math.cos(angle) * speed, math.sin(angle) * speed]
                particles.append(particles_m.Particle(eye_base[0], eye_base[1], 'red_light', vel, 0.2, 1.5 + random.randint(0, 20) / 10, custom_color=CYBER_COLORS['primary_green']))
        if (last < 1200) and (events['lv3timer'] >= 1200):
            player_message = [200, CYBER_MESSAGES['more_attacks'], '']
    
    if reset:
        if soul_mode:
            soul_mode = 0
            play_sound('exit_soul')
            particle_burst(player.center, 50)
            player.pos = soul.pos.copy()
            particle_burst(player.center, 50)
            scroll_target = player.pos
            player_velocity[1] = 0

    # projectiles
    if not soul_mode:
        r = player.rect
    else:
        r = pygame.Rect(soul.center[0] - 3, soul.center[1] - 7, 7, 7)
    
    projectiles_removed = 0
    for i, projectile in enumerate(projectiles):
        if len(projectile) == 3:
            projectile.append(random.random() + 1)
        projectile[0][0] += projectile[1][0] * 0.2 * dt
        projectile[0][1] += projectile[1][1] * 0.2 * dt
        
        if (projectile[0][0] < scroll[0] - 50 or projectile[0][0] > scroll[0] + display.get_width() + 50 or
            projectile[0][1] < scroll[1] - 50 or projectile[0][1] > scroll[1] + display.get_height() + 50):
            if projectile[2] == 'enemy':
                projectiles_removed += 1
        
        if not map_transition:
            if projectile[2] == 'enemy':
                if not death:
                    if r.collidepoint(projectile[0]):
                        play_sound('death')
                        death = 1
                        soul_mode = 0
                        scroll_target = scroll_target.copy()
                        for j in range(30):
                            sparks.append([list(r.center), math.radians(random.randint(1, 360)), 5 + random.randint(0, 30) / 10, 4, CYBER_COLORS['danger']])
                        for j in range(120):
                            angle = random.randint(1, 360)
                            speed = random.randint(70, 250) / 10
                            vel = [math.cos(angle) * speed, math.sin(angle) * speed]
                            particles.append(particles_m.Particle(r.center[0], r.center[1], 'light', vel, 0.4, 2 + random.randint(0, 20) / 10, custom_color=CYBER_COLORS['danger']))
                render_threat_warning(projectile, scroll, game_time)
    
    if projectiles_removed > 0:
        for _ in range(projectiles_removed):
            game_history.add_threat_neutralized()
    
    if level_name != 'level_3':
        projectiles = projectiles[-300:]
    else:
        projectiles = projectiles[-500:]

    if (events['lv1'] or level_name != 'level_1') and (not map_transition) and (events['lv3timer'] < 6300) and (level_name != 'level_4'):
        rate = 25
        if (level_name == 'level_2') and ((240 < events['lv2timer'] < 840) or (1200 < events['lv2timer'] < 1760) or (2000 < events['lv2timer'] < 2600)):
            rate = 12
        if random.randint(0, rate) == 0:
            vel = [random.randint(0, 20) / 10 - 1, 4]
            angle = math.atan2(vel[1], vel[0])
            spawn = [display.get_width() * random.random() + scroll[0], scroll[1]]
            for i in range(5):
                sparks.append([spawn.copy(), angle + math.radians(random.randint(0, 80) - 40), 4 + random.randint(0, 30) / 10, 6, CYBER_COLORS['danger']])
            projectiles.append([spawn, vel, 'enemy'])
            play_sound('eye_shoot')

    # sparks
    for i, spark in sorted(enumerate(sparks), reverse=True):
        advance(spark[0], spark[1], spark[2] * dt)
        spark[2] -= 0.2 * dt
        if spark[2] < 0:
            sparks.pop(i)
            continue
        point_list = [
            advance(spark[0].copy(), spark[1], spark[2] * spark[3]),
            advance(spark[0].copy(), spark[1] + math.pi / 2, spark[2] * spark[3] * 0.1),
            advance(spark[0].copy(), spark[1] + math.pi, spark[2] * spark[3] * 0.6),
            advance(spark[0].copy(), spark[1] - math.pi / 2, spark[2] * spark[3] * 0.1),
        ]
        point_list = [[p[0] - scroll[0], p[1] - scroll[1]] for p in point_list]
        pygame.draw.polygon(display, spark[4], point_list)

    # border fog
    fog_surf = pygame.Surface((display.get_width(), 24))
    pygame.draw.polygon(fog_surf, (0, 5, 10), b_points)
    fog_surf.set_alpha(150)
    fog_surf.set_colorkey((0, 0, 0))
    display.blit(pygame.transform.flip(fog_surf, True, False), (0, -6))
    display.blit(fog_surf, (0, 0))
    display.blit(pygame.transform.flip(fog_surf, True, True), (0, display.get_height() - 24 + 6))
    display.blit(pygame.transform.flip(fog_surf, False, True), (0, display.get_height() - 24))
    side_fog = pygame.transform.scale(pygame.transform.rotate(fog_surf, 90), (24, display.get_height()))
    display.blit(pygame.transform.flip(side_fog, False, True), (-6, 0))
    display.blit(side_fog, (0, 0))
    display.blit(pygame.transform.flip(side_fog, True, True), (display.get_width() - 24, 0))
    display.blit(pygame.transform.flip(side_fog, True, False), (display.get_width() - 24 + 6, 0))

    # particles
    for i, particle in sorted(enumerate(particles), reverse=True):
        alive = particle.update(0.1 * dt)
        particle.draw(display, scroll)
        if particle.type == 'light' and particle.time_left > 0:
            circle_size = max(1, 5 + particle.time_left * 0.5 * (math.sin(particle.random_constant * game_time * 0.01) + 3))
            particles_m.blit_center_add(display, particles_m.circle_surf(circle_size, (0, 1 + particle.time_left * 0.4, 4 + particle.time_left * 0.8)), (particle.x - scroll[0], particle.y - scroll[1]))
        if particle.type == 'red_light' and particle.time_left > 0:
            circle_size = max(1, 5 + particle.time_left * 0.5 * (math.sin(particle.random_constant * game_time * 0.01) + 3))
            particles_m.blit_center_add(display, particles_m.circle_surf(circle_size, (8 + particle.time_left * 0.6, 1 + particle.time_left * 0.2, 4 + particle.time_left * 0.4)), (particle.x - scroll[0], particle.y - scroll[1]))
        if not alive:
            particles.pop(i)

    # door vfx
    if door:
        particles_m.blit_center_add(display, particles_m.circle_surf(7 + 4 * (math.sin(game_time * 0.15) + 3), (0, 20, 12)), (door[0] + 6 - scroll[0], door[1] + 9 - scroll[1]))
        render_firewall([door[0] - scroll[0] + 6, door[1] - scroll[1] + 9], size=[2, 3], color1=(0, 50, 1), color2=CYBER_COLORS['safe'])

    # render soul
    if soul_mode:
        soul.render(display, scroll)

    # gui
    if player_message[0] and not death:
        player_message[0] -= 1
        if player_message[0] % 3 == 0:
            if player_message[2] != player_message[1]:
                play_sound('thought')
            player_message[2] = player_message[1][:len(player_message[2]) + 1]
        player_bubble_size += (1 - player_bubble_size) / 5
    else:
        player_bubble_size += (0 - player_bubble_size) / 5
        player_message[2] = player_message[2][:-1]
    relative_positions = [
        [-4, -3],
        [-14, -7],
        [-30, -17],
    ]
    for i, p in enumerate(player_bubble_positions):
        if not soul_mode:
            p[0] += (player.pos[0] + relative_positions[i][0] - p[0]) / (3 + i * 3)
            p[1] += (player.pos[1] + relative_positions[i][1] - p[1]) / (3 + i * 3)
        else:
            p[0] += (soul.pos[0] + relative_positions[i][0] - p[0]) / (3 + i * 3)
            p[1] += (soul.pos[1] + relative_positions[i][1] - p[1]) / (3 + i * 3)
    if player_bubble_size > 0.05:
        for i, p in enumerate(player_bubble_positions):
            points = []
            if i == 2:
                i = 6
            for j in range(8):
                points.append(advance(p.copy(), j / 8 * math.pi * 2, player_bubble_size * (i + 2)))
            points = [[p[0] - scroll[0], p[1] - scroll[1]] for p in points]
            if i == 6:
                for j, p2 in enumerate(points):
                    if (j < 2) or (j > 5):
                        p2[0] += font.width(player_message[1]) * player_bubble_size

            pygame.draw.polygon(display, (0, 10, 20), points)
            pygame.draw.polygon(display, CYBER_COLORS['primary_cyan'], points, 1)

            if i == 6:
                font.render(player_message[2], display, [p[0] - scroll[0], p[1] - scroll[1] - 3])

    # Tutoriales
    if tutorial < 200:
        if tutorial != 0:
            tutorial += (display.get_width() - tutorial) / 7
        black_font.render('Arrow keys to navigate', display, (display.get_width() // 2 + tutorial - font.width('Arrow keys to navigate') // 2 + 1, display.get_height() // 2 - 10))
        blue_font.render('Arrow keys to navigate', display, (display.get_width() // 2 + tutorial - font.width('Arrow keys to navigate') // 2, display.get_height() // 2 - 11))
        font.render('Arrow keys to navigate', display, (display.get_width() // 2 + tutorial - font.width('Arrow keys to navigate') // 2, display.get_height() // 2 - 12))
    if tutorial_2 < 200:
        if tutorial_2 > 0:
            tutorial_2 += (display.get_width() - tutorial_2) / 7
        if tutorial_2 != -1:
            black_font.render('Down arrow: deploy scanner', display, (display.get_width() // 2 + tutorial_2 - font.width('Down arrow: deploy scanner') // 2 + 1, display.get_height() // 2 - 10))
            blue_font.render('Down arrow: deploy scanner', display, (display.get_width() // 2 + tutorial_2 - font.width('Down arrow: deploy scanner') // 2, display.get_height() // 2 - 11))
            font.render('Down arrow: deploy scanner', display, (display.get_width() // 2 + tutorial_2 - font.width('Down arrow: deploy scanner') // 2, display.get_height() // 2 - 12))
    if level_name == 'level_4':
        black_font.render('System Secured!', display, (display.get_width() // 2 - font.width('System Secured!') // 2 + 1, display.get_height() // 2 - 10))
        blue_font.render('System Secured!', display, (display.get_width() // 2 - font.width('System Secured!') // 2, display.get_height() // 2 - 11))
        font.render('System Secured!', display, (display.get_width() // 2 - font.width('System Secured!') // 2, display.get_height() // 2 - 12))
    
    # UI de Puzzle
    if puzzle_input_active:
        box_width = 200
        box_height = 30
        box_x = display.get_width() // 2 - box_width // 2
        box_y = display.get_height() - 60
        
        pygame.draw.rect(display, (20, 40, 60), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(display, CYBER_COLORS['primary_cyan'], (box_x, box_y, box_width, box_height), 2)
        
        input_text = puzzle_user_input if puzzle_user_input else '_'
        blue_font.render(input_text, display, (box_x + 5, box_y + 10))
        
        if game_time % 30 < 15:
            cursor_x = box_x + 5 + font.width(puzzle_user_input)
            pygame.draw.rect(display, CYBER_COLORS['primary_green'], (cursor_x, box_y + 10, 2, 10))
        
        hint_text = "Soy un sistema que vigila quien entra y quien sale en una red. Enter: Enviar - ESC: Cancelar"
        font.render(hint_text, display, (display.get_width() // 2 - font.width(hint_text) // 2, box_y - 15))

    # HUD
    render_cyber_hud(player_mana, level_time)
    
    no_firewall = ''
    if not player_mana:
        no_firewall = 'no '
    black_font.render(no_firewall + 'firewall', display, (5, 6))
    if player_mana:
        blue_font.render(no_firewall + 'firewall', display, (5, 5))
    else:
        red_font.render(no_firewall + 'firewall', display, (5, 5))
    font.render(no_firewall + 'firewall', display, (5, 4))

    for i in range(player_mana):
        render_firewall([10 + i * 16, 18])

    # Mostrar objetivos del nivel si corresponde
    if show_level_objectives and not objectives_dismissed:
        render_level_objectives(level_name, game_time)

    if zoom == 1:
        screen.blit(pygame.transform.scale(display, screen.get_size()), (0, 0))
    else:
        size = [int(display.get_width() / zoom), int(display.get_height() / zoom)]
        screen.blit(pygame.transform.scale(clip(display, (display.get_width() - size[0]) // 2, (display.get_height() - size[1]) // 2, size[0], size[1]), screen.get_size()), (0, 0))

    if map_transition:
        black_surf = pygame.Surface(display.get_size()).convert_alpha()
        if map_transition < 60:
            black_surf.set_alpha(map_transition / 60 * 255)
        else:
            black_surf.set_alpha((1 - (map_transition - 60) / 60) * 255)
        screen.blit(pygame.transform.scale(black_surf, screen.get_size()), (0, 0))
    
    pygame.display.update()
    clock.tick(60)