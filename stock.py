# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import ModelView, Workflow, fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.i18n import gettext
from trytond.exceptions import UserError

__all__ = ['Location', 'Move']


class Location(metaclass=PoolMeta):
    __name__ = 'stock.location'
    outputs_group = fields.Many2One('res.group', 'Outputs Group',
        help='If defined only users from this group will be allowed to make '
        'moves from this location')
    inputs_group = fields.Many2One('res.group', 'Inputs Group',
        help='If defined only users from this group will be allowed to make '
        'moves to this location')

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
                raise UserError(
                    gettext('stock_location_group.msg_no_permissions_for_output_moves',
                    location=location.rec_name))

    @classmethod
    def check_location_outputs_group(cls, locations):
        return cls._check_location_group(locations, 'outputs')

    @classmethod
    def check_location_inputs_group(cls, locations):
        return cls._check_location_group(locations, 'inputs')


class Move(metaclass=PoolMeta):
    __name__ = 'stock.move'

    @classmethod
    @ModelView.button
    @Workflow.transition('done')
    def do(cls, moves):
        Location = Pool().get('stock.location')

        from_locations, to_locations = set(), set()
        for move in moves:
            if move.internal_quantity:
                from_locations.add(move.from_location)
                to_locations.add(move.to_location)
        Location.check_location_inputs_group(to_locations)
        Location.check_location_outputs_group(from_locations)

        super().do(moves)
