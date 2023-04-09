import json
from enum import Enum
from abc import ABC, abstractmethod


def pretty_print(obj):
    print(json.dumps(obj, indent=4))


def get_source_info_from_db(s_id):
    with open('specific_settings.json', 'r') as f:
        data = json.load(f)
        for d in data:
            yield d
    # return data[0]


class Settings(ABC):
    class Keys:
        check = 'c'
        img = 'i'
        yazar = 'y'
        title = 't'
        desc = 'd'

    def __init__(self, _id):
        self._id = _id
        source = self._get_source_info()

        self._gazete = source.get('gazete')
        self._base_url = source.get('url')
        self._country = source.get('country')
        self._settings = source.get('settings')

    @abstractmethod
    def _get_source_info(self) -> dict:
        pass

    @property
    def img(self):
        return self._settings[self.Keys.img]

    @property
    def title(self):
        return self._settings[self.Keys.title]

    @property
    def yazar(self):
        return self._settings[self.Keys.yazar]

    @property
    def desc(self):
        return self._settings[self.Keys.desc]

    @property
    def settings(self):
        return self._settings


class ListSettings(Settings):
    class ListKeys:
        list = 'l'
        url = 'u'
        url_index = 'u_i'

    @property
    def list(self):
        return self._settings[self.ListKeys.list]

    @property
    def url(self):
        return self._settings[self.ListKeys.url]

    @property
    def url_index(self):
        return self._settings[self.ListKeys.url_index]

    def __init__(self, s_id):
        super().__init__(s_id)

    def _get_source_info(self) -> dict:
        source_infos = get_source_info_from_db(self._id)
        for source_info in source_infos:
            prev_settings = json.loads(source_info.get('settings', '{}')).get('list', {})
            source_info['settings'] = {
                self.Keys.check: prev_settings.get('TagCheck'),
                self.Keys.img: prev_settings.get('TagImg'),
                self.Keys.yazar: prev_settings.get('TagYazar'),
                self.Keys.title: prev_settings.get('TagTitle'),
                self.Keys.desc: prev_settings.get('TagDesc')
            }

            source_info['settings'][self.ListKeys.list] = prev_settings.get('TagList')
            source_info['settings'][self.ListKeys.url] = prev_settings.get('TagUrl')
            source_info['settings'][self.ListKeys.url_index] = prev_settings.get('TagUrlIndex')

        return {}


class ContentSettings(Settings):
    class ContentKeys:
        content = 'con'
        is_content_p = 'is_c_p'
        is_content_none = 'is_c_n'
        remove_tags = 'r_t'

    def __init__(self, s_id):
        super().__init__(s_id)

    @property
    def content(self):
        return self._settings[self.ContentKeys.content]

    @property
    def is_content_p(self):
        return self._settings[self.ContentKeys.is_content_p]

    @property
    def is_content_none(self):
        return self._settings[self.ContentKeys.is_content_none]

    @property
    def remove_tags(self):
        return self._settings[self.ContentKeys.remove_tags]

    def _get_source_info(self) -> dict:
        source_infos = get_source_info_from_db(self._id)
        for source_info in source_infos:
            prev_settings = json.loads(source_info.get('settings', '{}')).get('list', {})
            source_info['settings'] = {
                self.Keys.check: prev_settings.get('TagHolder'),
                self.Keys.img: prev_settings.get('TagImg'),
                self.Keys.yazar: prev_settings.get('TagYazar'),
                self.Keys.title: prev_settings.get('TagTitle'),
                self.Keys.desc: prev_settings.get('TagDesc')
            }

            source_info['settings'][self.ContentKeys.content] = prev_settings.get('TagContent')
            source_info['settings'][self.ContentKeys.is_content_p] = prev_settings.get('isContentParagraph')
            source_info['settings'][self.ContentKeys.is_content_none] = prev_settings.get('isContentNone')
            source_info['settings'][self.ContentKeys.remove_tags] = prev_settings.get('TagsRemove')

        return {}


def process_list_request():
    settings = ListSettings(1)
    pretty_print(settings.settings)


def process_content_request():
    settings = ContentSettings(2)
    pretty_print(settings.settings)


if __name__ == '__main__':
    process_list_request()
    process_content_request()
