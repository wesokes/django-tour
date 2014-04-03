"""
Custom template tags for displaying tour navigation
"""
from django import template
from django.template.loader import get_template
import json
from tour.api import TourResource
from tour.models import Tour


register = template.Library()


@register.tag
def tour_navigation(parser, token):
    """
    Creates a hidden field for EXT that contains a serialized json object of the authenticated account.
    """
    return TourNavigationNode()


class TourNavigationNode(template.Node):
    """
    The rendering code for the ext_auth_account tag.
    """
    def render(self, context):
        if 'request' in context and hasattr(context['request'], 'user'):
            # Make sure this isn't the anonymous user
            if not context['request'].user.id:
                return ''

            # Check for any tours
            tour_class = Tour.objects.get_for_user(context['request'].user)

            # Add tour to the template if it exists
            if tour_class:
                # Serialize the tour and its steps
                tour = tour_class.tour
                tour_resource = TourResource()
                tour_bundle = tour_resource.build_bundle(obj=tour, request=context['request'])
                tour_data = tour_resource.full_dehydrate(tour_bundle)
                tour_json = tour_resource.serialize(None, tour_data, 'application/json')
                tour_dict = json.loads(tour_json)

                # Set the step css classes
                previous_steps_complete = True
                for step_dict in tour_dict['steps']:
                    cls = ''
                    if step_dict['url'] == context['request'].path:
                        cls += 'current '
                        step_dict['current'] = True
                    if not previous_steps_complete:
                        cls += 'incomplete unavailable '
                        step_dict['url'] = '#'
                    elif not step_dict['complete']:
                        cls += 'incomplete available '
                        previous_steps_complete = False
                    else:
                        cls += 'complete '
                    step_dict['cls'] = cls

                context['tour'] = tour_dict

            # Load the tour template and render it
            tour_template = get_template('tour/tour_navigation.html')
            return tour_template.render(context)
        return ''
