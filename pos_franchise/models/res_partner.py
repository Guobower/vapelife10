from openerp import models, fields, api, _,SUPERUSER_ID

class ResPartner(models.Model):
    _inherit = "res.partner"

    user_id = fields.Many2one('res.users', 
       track_visibility='onchange',
      string='Salesperson',default=lambda self:self.env.user,
      help='The internal user that is in charge of communicating with this contact if any.')

    @api.model
    def create_from_ui(self, partner):
        """ create or modify a partner from the point of sale ui.
            partner contains the partner's fields. """
        # image is a dataurl, get the data after the comma
        if partner.get('image'):
            partner['image'] = partner['image'].split(',')[1]
        partner_id = partner.pop('id', False)
        if partner_id:  # Modifying existing partner
            self.browse(partner_id).write(partner)
        else:
            partner['lang'] = self.env.user.lang
            partner['user_id'] = self.env.user.id
            partner_id = self.create(partner).id
        return partner_id

    