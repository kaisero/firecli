import json
from logging import getLogger
from pathlib import Path

from fireREST import FMC

logger = getLogger()


class Cache(object):
    def __init__(self, directory: str, api=None):
        self.api = api
        self.directory = self._init_directory(directory)
        self.cache = None
        self.cache_type = 'generic'

    @staticmethod
    def _init_directory(directory: str):
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
        return path

    def download(self):
        return

    def load(self):
        cache = dict()
        for f in self.directory.iterdir():
            if f.is_file() and f.suffix == '.json':
                logger.debug('Loading cache file %s', f)
                with open(f, 'r') as data:
                    cache[f.stem] = json.load(data)
        self.cache = cache
        return self.cache

    def save(self):
        for name, data in self.cache.items():
            filename = f'{name}.json'
            filepath = Path.joinpath(self.directory, filename)
            with open(filepath, 'w') as f:
                f.write(json.dumps(data, indent=4, ensure_ascii=False, sort_keys=True))


class ObjectCache(Cache):
    def __init__(self, directory: str, api=None):
        self.api = api
        self.directory = self._init_directory(f'{directory}/objects')
        self.cache = None
        self.cache_type = 'object'

    def download(self):
        fmc = self.api.fmc  # type: FMC
        cache = {
            'country': fmc.object.country.get(),
            'fqdn': fmc.object.fqdn.get(),
            'host': fmc.object.host.get(),
            'icmpv4object': fmc.object.icmpv4object.get(),
            'icmpv6object': fmc.object.icmpv6object.get(),
            'network': fmc.object.network.get(),
            'networkgroup': fmc.object.networkgroup.get(),
            'range': fmc.object.range.get(),
            'protocolportobject': fmc.object.protocolportobject.get(),
            'portobjectgroup': fmc.object.portobjectgroup.get(),
            'url': fmc.object.url.get(),
            'urlgroup': fmc.object.urlgroup.get(),
            'vlantag': fmc.object.vlantag.get(),
            'vlangrouptag': fmc.object.vlangrouptag.get(),
        }
        for obj in cache['host']:
            if 'overridable' in obj:
                if obj['overridable']:
                    obj['overrides'] = fmc.object.host.override.get(container_uuid=obj['id'])
        for obj in cache['range']:
            if 'overridable' in obj:
                if obj['overridable']:
                    obj['overrides'] = fmc.object.range.override.get(container_uuid=obj['id'])
        for obj in cache['network']:
            if 'overridable' in obj:
                if obj['overridable']:
                    obj['overrides'] = fmc.object.network.override.get(container_uuid=obj['id'])
        for obj in cache['networkgroup']:
            if 'overridable' in obj:
                if obj['overridable']:
                    obj['overrides'] = fmc.object.networkgroup.override.get(container_uuid=obj['id'])
        self.cache = cache


class PolicyCache(Cache):
    def __init__(self, directory: str, api=None):
        self.api = api
        self.directory = self._init_directory(f'{directory}/policies')
        self.cache = None
        self.cache_type = 'policy'

    def download(self):
        fmc = self.api.fmc  # type: FMC
        cache = {'accesspolicy': fmc.policy.accesspolicy.get(), 'prefilterpolicy': fmc.policy.prefilterpolicy.get()}
        for key, accesspolicy in enumerate(cache['accesspolicy']):
            accessrules = fmc.policy.accesspolicy.accessrule.get(container_uuid=accesspolicy['id'])
            cache['accesspolicy'][key]['rules'] = accessrules

        for key, prefilterpolicy in enumerate(cache['prefilterpolicy']):
            accessrules = fmc.policy.prefilterpolicy.accessrule.get(container_uuid=prefilterpolicy['id'])
            cache['prefilterpolicy'][key]['rules'] = accessrules

        self.cache = cache


class FmcCache(Cache):
    def __init__(self, directory: str, api=None):
        self.api = api
        self.directory = self._init_directory(directory)
        self.cache = {'objects': ObjectCache(directory, api), 'policies': PolicyCache(directory, api)}
        self.cache_type = 'FMC'

    def download(self):
        for _key, item in self.cache.items():
            item.download()

    def load(self):
        for _key, item in self.cache.items():
            item.load()
        return self.cache

    def save(self):
        for _key, item in self.cache.items():
            item.save()
