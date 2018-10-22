# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.modules.stock.location import STATES, DEPENDS

__all__ = ['Location', 'Move']
__metaclass__ = PoolMeta


class Location:
    __name__ = 'stock.location'
    __metaclass__ = PoolMeta
    outputs_group = fields.Many2One('res.group', 'Outputs Group',
        states=STATES, depends=DEPENDS,
        help='If defined only users from this group will be allowed to make '
        'moves from this location')
    inputs_group = fields.Many2One('res.group', 'Inputs Group',
        states=STATES, depends=DEPENDS,
        help='If defined only users from this group will be allowed to make '
        'moves to this location')

    @classmethod
    def __setup__(cls):
        super(Location, cls).__setup__()
        cls._error_messages.update({
                'no_permissions_for_output_moves': (
                    'You do not have permissions to move products from location '
                    '"%s".'),
                })

    @classmethod
    def _check_location_group(cls, locations, type_):
        pool = Pool()
        User = pool.get('res.user')
        user_id = Transaction().user
        if user_id == 0:
            return
        groups = set(User(user_id).groups)
        field_name = '%s_group' % type_
        for location in locations:
            group = getattr(location, field_name)
            if not group:
                continue
            if group not in groups:
                cls.raise_user_error('no_permissions_for_output_moves',
                    location.rec_name)

    @classmethod
    def check_location_outputs_group(cls, locations):
        return cls._check_location_group(locations, 'outputs')

    @classmethod
    def check_location_inputs_group(cls, locations):
        return cls._check_location_group(locations, 'inputs')


class Move:
    __name__ = 'stock.move'

    @classmethod
    def validate(cls, moves):
        pool = Pool()
        Location = pool.get('stock.location')
        super(Move, cls).validate(moves)
        from_locations, to_locations = set(), set()
        for move in moves:
            if move.state == 'done' and move.internal_quantity:
                from_locations.add(move.from_location)
                to_locations.add(move.to_location)
        Location.check_location_inputs_group(to_locations)
        Location.check_location_outputs_group(from_locations)
