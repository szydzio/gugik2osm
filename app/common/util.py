from copy import deepcopy
from lxml import etree
import mercantile as m
from mercantile import Tile, bounds
from pyproj import Proj, transform


notes = {
    'zbior': 'Modele 3D Budynków',
    'zrodlo': 'www.geoportal.gov.pl',
    'dysponent': 'Główny Geodeta Kraju',
    'data_pobrania_zbioru': '2019-11-10',
    'zakres_przetworzenia': 'Geometria budynków została spłaszczona do 2D oraz wyekstrahowana została część poligonowa wykorzystana dalej jako obrys budynku.',
    'informacja': '''Modele 3D budynków nie stanowią rejestru publicznego ani elementu treści takiego rejestru. W konsekwencji czego mają wartość jedynie poglądową. Niezgodność Modeli 3D budynków ze stanem faktycznym lub prawnym, tak w postaci nieprzetworzonej jak i po ich ewentualnym przetworzeniu w procesie ponownego wykorzystania, nie może stanowić podstawy odpowiedzialności Głównego Geodety Kraju z jakiegokolwiek tytułu wobec jakiegokolwiek podmiotu.''',
    'licencja': r'https://integracja.gugik.gov.pl/Budynki3D/GUGiK_Licencja_na_Budynki3D.pdf'
}
BUILDING_TAG = etree.Element('tag', k='building', v='yes')
SOURCE_BUILDING = etree.Element('tag', k='source', v='www.geoportal.gov.pl')
SOURCE_ADDR = etree.Element('tag', k='source:addr', v='gugik.gov.pl')


def to_merc(bbox: m.LngLatBbox) -> dict:
    """Method reprojects BBox in WGS84 (latitude, longitude) to Web Mercator."""
    in_proj = Proj('epsg:4326')
    out_proj = Proj('epsg:3857')
    res = dict()
    res["west"], res["south"] = transform(in_proj, out_proj, bbox.south, bbox.west)
    res["east"], res["north"] = transform(in_proj, out_proj, bbox.north, bbox.east)
    return res


def addresses_nodes(list_of_tuples: list) -> etree.Element:
    i = -1  # counter for fake ids
    for t in list_of_tuples:
        el = etree.Element('node', id=str(i), lat=str(t[8]), lon=str(t[7]))
        el.append(deepcopy(SOURCE_ADDR))
        # do not add 'ref:addr' tag
        # el.append(etree.Element('tag', k='ref:addr', v=t[0]))
        el.append(etree.Element('tag', k='addr:city:simc', v=t[2]))
        if t[3]:
            el.append(etree.Element('tag', k='addr:city', v=t[1]))
            el.append(etree.Element('tag', k='addr:street', v=t[3]))
            el.append(etree.Element('tag', k='addr:street:sym_ul', v=t[4]))
        else:
            el.append(etree.Element('tag', k='addr:place', v=t[1]))
        el.append(etree.Element('tag', k='addr:housenumber', v=t[5]))
        if t[6]:
            el.append(etree.Element('tag', k='addr:postcode', v=t[6]))
        i -= 1
        yield el


def buildings_nodes(list_of_tuples: list) -> etree.Element:
    i = -100000  # counter for fake ids
    n = {}  # list of nodes
    lst = []  # list of ways
    # cursor returns tuple of (way_id, array_of_points[])
    for t in list_of_tuples:
        # create 'way' node for xml tree
        way = etree.Element('way', id=str(t[0]))
        way.append(deepcopy(BUILDING_TAG))
        way.append(deepcopy(SOURCE_BUILDING))

        # iterate over array of points that make the polygon and add references to them to the way xml node
        for xy in t[1]:
            # if given point is already in our list of nodes then:
            if n.get(tuple(xy)):
                way.append(deepcopy(n[tuple(xy)]['el']))
                # appending doesn't work when you try to pass the same object
                # you need to create new object if you want nodes with duplicate values
                # since polygons start and end with the same node we need to deepcopy the object
            else:
                temp = etree.Element('nd', ref=str(i))
                way.append(temp)
                n[tuple(xy)] = {'el': temp, 'id': i}
            i -= 1
        lst.append(way)

    for k, v in n.items():
        yield etree.Element('node', id=str(v['id']), lat=str(k[1]), lon=str(k[0]))

    for w in lst:
        yield w


def addresses_xml(list_of_tuples):
    """Method creates XML with address points in OSM schema."""
    root = etree.Element('osm', version='0.6')
    i = -1  # counter for fake ids
    for t in list_of_tuples:
        el = etree.Element('node', id=str(i), lat=str(t[8]), lon=str(t[7]))
        el.append(deepcopy(SOURCE_ADDR))
        # do not add 'ref:addr' tag
        # el.append(etree.Element('tag', k='ref:addr', v=t[0]))
        el.append(etree.Element('tag', k='addr:city:simc', v=t[2]))
        if t[3]:
            el.append(etree.Element('tag', k='addr:city', v=t[1]))
            el.append(etree.Element('tag', k='addr:street', v=t[3]))
            el.append(etree.Element('tag', k='addr:street:sym_ul', v=t[4]))
        else:
            el.append(etree.Element('tag', k='addr:place', v=t[1]))
        el.append(etree.Element('tag', k='addr:housenumber', v=t[5]))
        if t[6]:
            el.append(etree.Element('tag', k='addr:postcode', v=t[6]))
        root.append(el)
        i -= 1
    return root


def buildings_xml(list_of_tuples):
    """Method creates XML with buildings (polygons) in OSM schema."""
    root = etree.Element('osm', version='0.6')
    i = -1  # counter for fake ids
    n = {}  # list of nodes
    lst = []  # list of ways
    # cursor returns tuple of (way_id, array_of_points[])
    for t in list_of_tuples:
        # create 'way' node for xml tree
        way = etree.Element('way', id=str(t[0]))
        way.append(deepcopy(BUILDING_TAG))
        way.append(deepcopy(SOURCE_BUILDING))

        # iterate over array of points that make the polygon and add references to them to the way xml node
        for xy in t[1]:
            # if given point is already in our list of nodes then:
            if n.get(tuple(xy)):
                way.append(deepcopy(n[tuple(xy)]['el']))
                # appending doesn't work when you try to pass the same object
                # you need to create new object if you want nodes with duplicate values
                # since polygons start and end with the same node we need to deepcopy the object
            else:
                temp = etree.Element('nd', ref=str(i))
                way.append(temp)
                n[tuple(xy)] = {'el': temp, 'id': i}
            i -= 1
        lst.append(way)

    for k, v in n.items():
        root.append(etree.Element('node', id=str(v['id']), lat=str(k[1]), lon=str(k[0])))

    for w in lst:
        root.append(w)

    return root
