"""Rockheap Mine: Coal can be selected, counted and planned.

Fixtures are crops of live EN 1280x720 screenshots, pasted back onto a black frame:
- list_top.png / list_bottom.png: the Select Product list (166, 68, 478, 652) at the top
  (Coal, Copper, Bauxite) and scrolled to the end (Bauxite, Iron, Sulfur, Silver);
- selected_coal.png: the right-hand panel (700, 200, 890, 360) with Coal selected, which is
  how the list opens.
"""
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np

import module.config.server as server

server.server = 'en'

from module.base.button import Button
from module.base.utils import load_image
from module.config.config_generated import GeneratedConfig
from module.island.island import Island
from module.island.island_mine_forest import IslandMineForest
import module.island_mine_forest.assets as assets
from module.island_planner import settings_map

FIXTURES = Path(__file__).parent / 'fixtures' / 'island_mine_en'
ORES = ['COPPER', 'ALUMINIUM', 'IRON', 'SULPHUR', 'SILVER']


def frame(name, area):
    x1, y1, x2, y2 = area
    image = np.zeros((720, 1280, 3), dtype=np.uint8)
    image[y1:y2, x1:x2] = load_image(str(FIXTURES / name))
    return image


def fresh(button):
    """Rebuild a button for the current server in case another test loaded it as cn."""
    return Button(area=button.raw_area, color=button.raw_color, button=button.raw_button,
                  file=button.raw_file, name=button.raw_name)


def island(image):
    obj = object.__new__(Island)
    obj.device = SimpleNamespace(image=image, stuck_record_add=lambda b: None)
    obj.interval_timer = {}
    obj.config = SimpleNamespace(SERVER='en', BUTTON_OFFSET=30)
    return obj


def in_list(name, fixture):
    button = fresh(getattr(assets, f'SELECT_{name}'))
    image = frame(fixture, (166, 68, 478, 652))
    return island(image).match_template_color(button, offset=300, similarity=0.85, threshold=10)


def selected(name):
    button = fresh(getattr(assets, f'SELECT_{name}_CHECK'))
    image = frame('selected_coal.png', (700, 200, 890, 360))
    # Same offset / similarity / colour threshold as IslandMineForest.is_product_confirmed
    return island(image).match_template_color(
        button, offset=IslandMineForest.PRODUCT_CONFIRM_OFFSET,
        similarity=IslandMineForest.PRODUCT_CONFIRM_SIMILARITY,
        threshold=IslandMineForest.PRODUCT_CONFIRM_THRESHOLD)


class CoalPictureTest(unittest.TestCase):
    def setUp(self):
        self._server = server.server
        server.server = 'en'

    def tearDown(self):
        server.server = self._server

    def test_coal_found_only_where_listed(self):
        self.assertTrue(in_list('COAL', 'list_top.png'))
        self.assertFalse(in_list('COAL', 'list_bottom.png'))

    def test_ores_still_found(self):
        for name, fixture in [('COPPER', 'list_top.png'), ('ALUMINIUM', 'list_top.png'),
                              ('IRON', 'list_top.png'), ('SULPHUR', 'list_bottom.png'),
                              ('SILVER', 'list_bottom.png')]:
            with self.subTest(name=name):
                self.assertTrue(in_list(name, fixture))

    def test_coal_selected_panel(self):
        self.assertTrue(selected('COAL'))

    def test_preselected_coal_not_taken_for_an_ore(self):
        # The list opens with Coal selected; choosing an ore must not be confirmed on that panel
        for name in ORES:
            with self.subTest(name=name):
                self.assertFalse(selected(name))


class CoalSettingsTest(unittest.TestCase):
    def test_coal_is_8_per_run(self):
        mine = object.__new__(IslandMineForest)
        self.assertEqual(mine._units_per_run('Coal'), 8)
        self.assertEqual(mine._units_per_run('Copper'), 4)
        self.assertEqual(IslandMineForest.PRODUCT_MAX_RUNS['Coal'], 12)

    def test_warehouse_name(self):
        self.assertIn('Coal', IslandMineForest.ITEM_CN_NAMES['Coal'])

    def test_planner_mine_products_supported(self):
        # Every mine product the planner may plan has a picture, a minimum stock option and a
        # Default ore option
        thresholds = settings_map.THRESHOLD_GROUPS['mine']
        for name, item_id in settings_map.PRODUCT_ITEM_IDS['mine'].items():
            with self.subTest(name=name):
                self.assertIn(name, IslandMineForest.PRODUCT_CONFIGS)
                path = thresholds[item_id]
                self.assertEqual(path, f'IslandMineForest.IslandMine.Min{name}')
                self.assertTrue(hasattr(GeneratedConfig, f'IslandMine_Min{name}'))
        self.assertEqual(GeneratedConfig.IslandMine_MinCoal, 0)


if __name__ == '__main__':
    unittest.main()
