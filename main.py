import asyncio
from os import PathLike
from typing import Union

from aiohttp import request

token = ''


class DynaPath(PathLike):

    def __init__(self, document_path: Union[str, list, 'DynaPath'], node_path: Union[str, list] = None):
        self.node_path = []
        self.document_path = []

        if isinstance(document_path, DynaPath):
            self.append(document_path)
        elif isinstance(document_path, (str, list)):
            self.append_document_path(document_path)
        else:
            raise TypeError('`document_path` must be of type str, list or DynaPath')

        if node_path:
            if isinstance(node_path, (str, list)):
                self.append_node_path(node_path)
            else:
                raise TypeError('`node_path` must be of type str or list')

        super().__init__()

    def __fspath__(self):
        return self.__str__()

    def __str__(self):
        return f'{"/".join(self.document_path)}:{"/".join(self.node_path)}'

    def append(self, tail: Union['DynaPath', str, list]):
        if isinstance(tail, DynaPath):
            self.append_document_path(tail.document_path)
            self.append_node_path(tail.node_path)
        elif isinstance(tail, (str, list)):
            self.append_node_path(tail)
        else:
            raise TypeError('`tail` must be of type str, list or DynaPath')

    def append_node_path(self, tail: Union[str, list]):
        append_or_extend(self.node_path, tail)

    def append_document_path(self, tail: Union[str, list]):
        append_or_extend(self.document_path, tail)

    def __truediv__(self, tail: Union['DynaPath', str, list]) -> 'DynaPath':
        self.append(tail)
        return self

    def __iter__(self):
        return self.node_path_elements()

    def node_path_elements(self):
        for itm in self.node_path:
            yield itm

    def document_path_elements(self):
        for itm in self.document_path:
            yield itm


def append_or_extend(head: list, tail: Union[list, str]):
    if not isinstance(head, list):
        raise TypeError('`head` must be of type list')
    if isinstance(tail, str):
        head.extend(tail.strip('/').split('/'))
    elif isinstance(tail, list):
        head.extend(tail)
    else:
        raise TypeError('`tail` must be of type str or list')


async def read_item(path: DynaPath):
    print(path)
    file_id = await get_document(path.document_path_elements())
    print(file_id)
    await get_node(file_id, path)


async def get_node(file_id: str, path: list):
    async with request('POST', 'https://dynalist.io/api/v1/doc/read', json={'token': token,
                                                                            'file_id': file_id}) as response:
        data = await response.json()
        nodes_tree = dict(map(lambda itm: (itm['id'], itm), data['nodes']))
        print(nodes_tree)
        children_ids = nodes_tree['root']['children']
        target = None
        for element in path:
            for node_id in children_ids:
                node = nodes_tree[node_id]
                if node['content'] == element:
                    children_ids = node.get('children', [])
                    target = node
                    break
        print(target)


async def get_document(document_path_elements: list):
    async with request('POST', 'https://dynalist.io/api/v1/file/list', json={'token': token}) as response:
        data = await response.json()
        root_file_id = data['root_file_id']
        files_tree = dict(map(lambda itm: (itm['id'], itm), data['files']))
        children_ids = files_tree[root_file_id]['children']
        target = None
        for element in document_path_elements:
            if target is not None:
                raise Exception('Document must be a last element of file path')
            for file_id in children_ids:
                file = files_tree[file_id]
                if file['title'] == element:
                    if file['type'] == 'folder':
                        children_ids = files_tree[root_file_id]['children']
                    else:
                        target = file_id
                    break

        return target


async def main():
    await read_item(DynaPath('Tasks') / 'Today' / 'Test' / 'Boop' / 'Nope' / 'Chop')


if __name__ == '__main__':
    asyncio.run(main())
