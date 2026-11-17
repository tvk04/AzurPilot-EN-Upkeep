"""Manufacturing: Chemicals, Clock, Gloves, Aroma Sachet and Choice Wooden Barrel can be selected.

Fixtures are crops of live EN 1280x720 screenshots, pasted back onto a black frame:
- list_*.png: the Select Product list (166, 68, 478, 652) of each production line, scrolled to
  the end (Industrial, Electronic, Arts & Crafts, Lumber);
- selected_*.png: the right-hand panel (700, 200, 890, 360) with the new product selected.
"""
import unittest
from pathlib import Path
from types import SimpleNamespace
import inspect

import numpy as np

import module.config.server as server

server.server = 'en'

from module.base.button import Button
from module.base.utils import load_image
from module.island.island import Island
from module.island.island_manufacture import SEASONAL_HANDMADE_ITEMS, IslandManufacture
import module.island_manufacture.assets as assets
from module.island_planner import settings_map

FIXTURES = Path(__file__).parent / 'fixtures' / 'island_manufacture_en'
NEW = {
    'CHEMICALS': 'industrial', 'CLOCK': 'electronic', 'GLOVES': 'handmade',
    'AROMA_SACHET': 'handmade', 'CHOICE_WOODEN_BARREL': 'lumber',
}
# Items already supported that share these lists: their pictures must still match, and the new
# pictures must not be confused with them
OLD = {
    'industrial': ['CHARCOAL_BRUSH', 'CABLE', 'IRON_NAIL'],
    'electronic': ['INK_CARTRIDGE'],
    'handmade': ['ROPE'],
    'lumber': ['PAPER', 'NOTEBOOK', 'CHAIR_DESK'],
}


def list_frame(line):
    image = np.zeros((720, 1280, 3), dtype=np.uint8)
    image[68:652, 166:478] = load_image(str(FIXTURES / f'list_{line}.png'))
    return image


def panel_frame(name):
    image = np.zeros((720, 1280, 3), dtype=np.uint8)
    image[200:360, 700:890] = load_image(str(FIXTURES / f'selected_{name.lower()}.png'))
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


def in_list(name, line):
    button = fresh(getattr(assets, f'SELECT_{name}'))
    return island(list_frame(line)).match_template_color(button, offset=300, similarity=0.85, threshold=10)


def selected(name, panel):
    button = fresh(getattr(assets, f'SELECT_{name}_CHECK'))
    return island(panel_frame(panel)).match_template_color(button, offset=20, similarity=0.85, threshold=10)


class NewProductPicturesTest(unittest.TestCase):
    def setUp(self):
        self._server = server.server
        server.server = 'en'

    def tearDown(self):
        server.server = self._server

    def test_new_products_found_only_in_their_own_list(self):
        for name, line in NEW.items():
            for other in ('industrial', 'electronic', 'handmade', 'lumber'):
                with self.subTest(name=name, list=other):
                    self.assertEqual(bool(in_list(name, other)), other == line)

    def test_old_products_still_found(self):
        for line, names in OLD.items():
            for name in names:
                with self.subTest(name=name):
                    self.assertTrue(in_list(name, line))

    def test_selected_panel_matches_only_its_product(self):
        for name in NEW:
            for panel in NEW:
                with self.subTest(picture=name, panel=panel):
                    self.assertEqual(bool(selected(name, panel)), name == panel)


class ProductListsAgreeTest(unittest.TestCase):
    def test_manufacture_task_and_planner_list_the_same_products(self):
        # every product the planner may write into <Line>.Products has an entry in the manufacture task
        source = inspect.getsource(IslandManufacture.__init__)
        for data in settings_map.MANUFACTURE_PRODUCTS.values():
            for name in data['products']:
                if name in SEASONAL_HANDMADE_ITEMS:
                    continue  # seasonal Handmade products are added at run time
                with self.subTest(product=name):
                    self.assertIn(f"'{name}'", source)

    def test_item_ids_match_game_names(self):
        from module.island_planner.data import DIC_ISLAND_ITEM
        expected = {'chemicals': 'Chemicals', 'clock': 'Clock', 'gloves': 'Gloves', 'aroma_sachet': 'Aroma Sachet',
                    'choice_wooden_barrel': 'Choice Wooden Barrel'}
        ids = {name: item_id for data in settings_map.MANUFACTURE_PRODUCTS.values()
               for name, item_id in data['products'].items()}
        for name, en in expected.items():
            self.assertEqual(DIC_ISLAND_ITEM[ids[name]]['name']['en'], en)


if __name__ == '__main__':
    unittest.main()
