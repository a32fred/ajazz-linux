"""DPI, sensor and lighting editors; every edit modifies a staged draft."""
import copy
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QCheckBox, QSlider, QColorDialog, QFormLayout)

from .widgets import label, button, combo, spin, card, row


class SensitivityPage(QWidget):
    edited = Signal()

    def __init__(self):
        super().__init__()
        self.settings = None
        self.loading = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        summaries = QHBoxLayout()
        summaries.addWidget(label('Active stage', 'muted'))
        self.dpi_summary = label('800', 'large')
        summaries.addWidget(self.dpi_summary)
        summaries.addWidget(label('DPI', 'unit'))
        summaries.addStretch()
        summaries.addWidget(label('Battery', 'muted'))
        self.battery = label('—', 'heading')
        summaries.addWidget(self.battery)
        layout.addLayout(summaries)
        dpi_card, content = card('DPI stages')
        self.stage_count = spin(1, 6, 'Number of DPI stages')
        content.addWidget(row(label('Number of stages', 'muted'), self.stage_count, stretch=True))
        self.stage_buttons = []
        stages = QHBoxLayout()
        for index in range(6):
            item = button(str(index + 1), lambda checked=False, i=index: self.select_stage(i))
            item.setCheckable(True)
            item.setAccessibleName(f'Select DPI stage {index + 1}')
            stages.addWidget(item)
            self.stage_buttons.append(item)
        content.addLayout(stages)
        self.x_dpi = spin(50, 26000, 'Horizontal DPI')
        self.y_dpi = spin(50, 26000, 'Vertical DPI')
        self.x_dpi.setSingleStep(50)
        self.y_dpi.setSingleStep(50)
        self.link_axes = QCheckBox('Link X and Y')
        self.link_axes.setChecked(True)
        content.addWidget(row(label('X DPI'), self.x_dpi, label('Y DPI'), self.y_dpi, self.link_axes, stretch=True))
        content.addWidget(label('50 — 26,000 DPI · steps of 50', 'muted'))
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setAccessibleName('DPI slider')
        self.slider.setRange(1, 520)
        content.addWidget(self.slider)
        self.stage_color = button('Stage color', self.choose_stage_color)
        content.addWidget(row(self.stage_color, stretch=True))
        layout.addWidget(dpi_card)
        sensor, content = card('Sensor & response')
        form = QFormLayout()
        form.setSpacing(12)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        self.polling = combo([(f'{v} Hz', v) for v in (125, 250, 500, 1000)], 'Polling rate')
        self.debounce = spin(0, 30, 'Debounce time', ' ms')
        self.lod = combo([('1 mm', 1), ('2 mm', 2)], 'Lift-off distance')
        for field in (self.polling, self.lod):
            field.setFixedWidth(112)
        form.addRow('Polling rate', self.polling)
        form.addRow('Debounce time', self.debounce)
        form.addRow('Lift-off distance', self.lod)
        content.addLayout(form)
        self.angle = QCheckBox('Angle snapping')
        self.ripple = QCheckBox('Ripple filtering')
        content.addWidget(row(self.angle, self.ripple, stretch=True))
        layout.addWidget(sensor)
        layout.addStretch()
        self.stage_count.valueChanged.connect(self.change_count)
        self.x_dpi.valueChanged.connect(lambda value: self.change_dpi('x', value))
        self.y_dpi.valueChanged.connect(lambda value: self.change_dpi('y', value))
        self.slider.valueChanged.connect(lambda value: self.x_dpi.setValue(value * 50))
        self.link_axes.toggled.connect(self.link_changed)
        self.polling.currentIndexChanged.connect(lambda _: self.scalar('polling_hz', self.polling.currentData()))
        self.lod.currentIndexChanged.connect(lambda _: self.scalar('lod_mm', self.lod.currentData()))
        self.debounce.valueChanged.connect(lambda value: self.scalar('debounce_ms', value))
        self.angle.toggled.connect(lambda value: self.scalar('angle_snapping', value))
        self.ripple.toggled.connect(lambda value: self.scalar('ripple', value))

    def load(self, settings):
        self.settings = settings
        self.loading = True
        self.stage_count.setValue(len(settings.stages))
        for control, value in ((self.polling, settings.polling_hz), (self.lod, settings.lod_mm)):
            control.setCurrentIndex(control.findData(value))
        self.debounce.setValue(settings.debounce_ms)
        self.angle.setChecked(settings.angle_snapping)
        self.ripple.setChecked(settings.ripple)
        self.load_stage()
        self.loading = False

    def load_stage(self):
        was_loading, self.loading = self.loading, True
        stage = self.settings.stages[self.settings.active_stage]
        self.x_dpi.setValue(stage.x)
        self.y_dpi.setValue(stage.y)
        self.slider.setValue(stage.x // 50)
        self.link_axes.setChecked(stage.x == stage.y)
        for index, item in enumerate(self.stage_buttons):
            item.setVisible(index < len(self.settings.stages))
            if index < len(self.settings.stages):
                value = self.settings.stages[index]
                item.setText(f'{index + 1}  ·  {value.x}')
                item.setChecked(index == self.settings.active_stage)
        self.stage_color.setText(f'Stage color  {stage.color.upper()}')
        swatch = QPixmap(16, 16)
        swatch.fill(QColor(stage.color))
        self.stage_color.setIcon(QIcon(swatch))
        self.dpi_summary.setText(str(stage.x) if stage.x == stage.y else f'{stage.x} × {stage.y}')
        self.loading = was_loading

    def select_stage(self, index):
        if self.settings and not self.loading:
            self.settings.active_stage = index
            self.load_stage()
            self.edited.emit()

    def change_count(self, count):
        if self.loading or self.settings is None:
            return
        while len(self.settings.stages) < count:
            self.settings.stages.append(copy.deepcopy(self.settings.stages[-1]))
        self.settings.stages = self.settings.stages[:count]
        self.settings.active_stage = min(self.settings.active_stage, count - 1)
        self.load_stage()
        self.edited.emit()

    def change_dpi(self, axis, value):
        if self.loading or self.settings is None:
            return
        value = max(50, min(26000, round(value / 50) * 50))
        stage = self.settings.stages[self.settings.active_stage]
        setattr(stage, axis, value)
        if self.link_axes.isChecked():
            stage.x = stage.y = value
        self.load_stage()
        self.edited.emit()

    def link_changed(self, linked):
        if linked and not self.loading:
            self.change_dpi('y', self.x_dpi.value())

    def choose_stage_color(self):
        chosen = QColorDialog.getColor(QColor(self.settings.stages[self.settings.active_stage].color), self, 'DPI stage color')
        if chosen.isValid():
            self.settings.stages[self.settings.active_stage].color = chosen.name()
            self.load_stage()
            self.edited.emit()

    def scalar(self, name, value):
        if not self.loading and self.settings is not None:
            setattr(self.settings, name, value)
            self.edited.emit()


class LightingPage(QWidget):
    edited = Signal()

    def __init__(self):
        super().__init__()
        self.settings = None
        self.loading = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        scroll, scroll_content = card('Scroll wheel light')
        scroll_content.addWidget(label('The scroll wheel shows the color of the active DPI stage '
                                       '(choose stage colors under Sensitivity).', 'muted'))
        self.dpi_mode = combo([('Off', 0), ('Steady', 1), ('Breathing', 2)], 'Scroll light effect')
        self.dpi_brightness = spin(1, 10, 'Scroll light brightness')
        self.dpi_speed = spin(1, 8, 'Scroll light breathing speed')
        self.dpi_form = QFormLayout()
        self.dpi_form.setSpacing(12)
        self.dpi_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        self.dpi_mode.setFixedWidth(160)
        self.dpi_form.addRow('Effect', self.dpi_mode)
        self.dpi_form.addRow('Brightness', row(self.dpi_brightness, label('of 10', 'unit'), stretch=True))
        self.dpi_form.addRow('Breathing speed', row(self.dpi_speed, label('1 slowest, 8 fastest', 'unit'), stretch=True))
        scroll_content.addLayout(self.dpi_form)
        self.dpi_missing = label('The mouse has not reported a scroll light setting, so it cannot be changed here.', 'muted')
        scroll_content.addWidget(self.dpi_missing)
        layout.addWidget(scroll)
        notice, notice_content = card('Main lighting')
        notice_content.addWidget(label('The supplied driver lists no main lighting effect for this model, and these '
                                       'controls have not been verified on it. Other mice that have one may use them.', 'muted'))
        self.experimental = QCheckBox('Enable experimental lighting controls')
        notice_content.addWidget(self.experimental)
        layout.addWidget(notice)
        effect, content = card('Main lighting (unverified)')
        self.effect_controls = effect
        self.light_on = QCheckBox('Lighting enabled')
        content.addWidget(self.light_on)
        self.mode = combo([('Steady', 1), ('Breathing', 2), ('Neon', 4), ('Color breathing', 6), ('Off', 0)], 'Lighting effect')
        self.brightness = spin(1, 10, 'Lighting brightness')
        self.speed = spin(1, 10, 'Lighting speed')
        self.color = button('Choose color', self.choose_color)
        self.form = QFormLayout()
        self.form.setSpacing(16)
        self.form.addRow('Effect', self.mode)
        self.form.addRow('Brightness', self.brightness)
        self.form.addRow('Speed', self.speed)
        self.form.addRow('Color', self.color)
        content.addLayout(self.form)
        self.hint = label('', 'muted')
        content.addWidget(self.hint)
        layout.addWidget(effect)
        behavior, content = card('When to light up')
        self.behavior_controls = behavior
        self.motion = QCheckBox('Turn lights off while moving')
        content.addWidget(self.motion)
        self.idle = combo([(f'{v} seconds' if v < 60 else f'{v // 60} minutes', v)
                           for v in (10, 30, 60, 300, 600, 900, 1200, 1500, 1800, 2100, 2400)], 'Idle light timeout')
        content.addWidget(row(label('Turn lights off after idle'), self.idle))
        layout.addWidget(behavior)
        effect.setEnabled(False)
        behavior.setEnabled(False)
        effect.hide()
        behavior.hide()
        self.experimental.toggled.connect(effect.setEnabled)
        self.experimental.toggled.connect(behavior.setEnabled)
        self.experimental.toggled.connect(effect.setVisible)
        self.experimental.toggled.connect(behavior.setVisible)
        layout.addStretch()
        self.dpi_brightness.valueChanged.connect(self.dpi_brightness_changed)
        self.dpi_speed.valueChanged.connect(self.dpi_speed_changed)
        self.dpi_mode.currentIndexChanged.connect(self.dpi_mode_changed)
        self.mode.currentIndexChanged.connect(self.mode_changed)
        self.light_on.toggled.connect(lambda value: self.scalar('light_on', value))
        self.motion.toggled.connect(lambda value: self.scalar('light_off_while_moving', value))
        self.idle.currentIndexChanged.connect(lambda _: self.scalar('idle_seconds', self.idle.currentData()))
        self.speed.valueChanged.connect(lambda value: self.light_scalar('speed', value))
        self.brightness.valueChanged.connect(lambda value: self.light_scalar('brightness', value))

    def load(self, settings):
        self.settings = settings
        self.loading = True
        self.load_dpi_effect(settings.dpi_effect)
        self.light_on.setChecked(settings.light_on)
        self.motion.setChecked(settings.light_off_while_moving)
        self.idle.setCurrentIndex(self.idle.findData(settings.idle_seconds))
        self.mode.setCurrentIndex(self.mode.findData(settings.lighting.mode))
        self.speed.setValue(settings.lighting.speed)
        self.brightness.setValue(settings.lighting.brightness)
        self.color.setText(settings.lighting.color.upper() + '  ·  Choose color')
        self.loading = False
        self.update_mode()

    def load_dpi_effect(self, effect):
        self.dpi_missing.setVisible(effect is None)
        for widget in (self.dpi_mode, self.dpi_brightness, self.dpi_speed):
            widget.setEnabled(effect is not None)
        if effect is None:
            return
        # A mode this app has not seen light up is kept as the mouse reported it.
        known = self.dpi_mode.findData(effect.mode)
        if known == -1:
            self.dpi_mode.addItem(f'Mode {effect.mode} (as reported)', effect.mode)
            known = self.dpi_mode.findData(effect.mode)
        for index in reversed(range(self.dpi_mode.count())):
            if self.dpi_mode.itemData(index) not in (0, 1, 2, effect.mode):
                self.dpi_mode.removeItem(index)
        self.dpi_mode.setCurrentIndex(self.dpi_mode.findData(effect.mode))
        self.dpi_brightness.setValue(effect.brightness)
        self.dpi_speed.setValue(min(max(effect.param, 1), 8))
        self.update_dpi_controls()

    def update_dpi_controls(self):
        effect = self.settings.dpi_effect if self.settings else None
        if effect is None:
            return
        self.dpi_brightness.setEnabled(effect.mode != 0)
        self.dpi_speed.setEnabled(effect.mode == 2)

    def dpi_mode_changed(self):
        if self.loading or not self.settings or not self.settings.dpi_effect:
            return
        effect = self.settings.dpi_effect
        effect.mode = self.dpi_mode.currentData()
        if effect.mode == 2 and not 1 <= effect.param <= 8:
            effect.param = 5
            self.loading = True
            self.dpi_speed.setValue(5)
            self.loading = False
        self.update_dpi_controls()
        self.edited.emit()

    def dpi_speed_changed(self, value):
        if not self.loading and self.settings and self.settings.dpi_effect:
            self.settings.dpi_effect.param = value
            self.edited.emit()

    def dpi_brightness_changed(self, value):
        if not self.loading and self.settings and self.settings.dpi_effect:
            self.settings.dpi_effect.brightness = value
            self.edited.emit()

    def update_mode(self):
        mode = self.mode.currentData()
        on = self.light_on.isChecked()
        self.mode.setEnabled(on)
        self.brightness.setEnabled(on and mode != 0)
        self.speed.setEnabled(on and mode not in (0, 1))
        self.color.setEnabled(on and mode in (1, 2))
        self.hint.setText('This effect chooses its own colors.' if mode in (4, 6) else
                          'Light parameters are retained while the effect is off.' if mode == 0 else
                          'Choose a color and brightness for this effect.')

    def mode_changed(self):
        if not self.loading and self.settings:
            self.settings.lighting.mode = self.mode.currentData()
            self.update_mode()
            self.edited.emit()

    def scalar(self, name, value):
        if not self.loading and self.settings:
            setattr(self.settings, name, value)
            self.update_mode()
            self.edited.emit()

    def light_scalar(self, name, value):
        if not self.loading and self.settings:
            setattr(self.settings.lighting, name, value)
            self.edited.emit()

    def choose_color(self):
        chosen = QColorDialog.getColor(QColor(self.settings.lighting.color), self, 'Lighting color')
        if chosen.isValid():
            self.settings.lighting.color = chosen.name()
            self.color.setText(chosen.name().upper() + '  ·  Choose color')
            self.edited.emit()
