from django import template
from django.utils.safestring import mark_safe

from ..models import Smartphone

register = template.Library()

TABLE_HEAD = '''
            <table class="table">
                <tbody>
             '''

TABLE_TAIL = '''
                </tbody>
             </table>
             '''

TABLE_CONTENT = """
                <tr>
                     <td>{name}</td>
                     <td>{value}</td>
                 </tr>
                """

PRODUCT_SPEC = {
    'notebook': {
        'Diagonal': 'diagonal',
        'Display type': 'display',
        'Processor freq': 'processor_freq',
        'RAM': 'ram',
        'Videocard': 'video',
        'Battery working time': 'time_without_charge'
    },
    'smartphone': {
        'Diagonal': 'diagonal',
        'Display type': 'display',
        'Resolution': 'resolution',
        'RAM': 'ram',
        'SD': 'sd',
        'Battery working time': 'accum_volume',
        'Sd capacity': 'sd_volume',
        'Main Camera': 'main_cam_mp',
        'Frontal Camera': 'frontal_cam_mp',
    }
}


def get_product_spec(product, model_name):
    table_content = ''
    for name, value in PRODUCT_SPEC[model_name].items():
        table_content += TABLE_CONTENT.format(name=name, value=getattr(product, value))
    return table_content


@register.filter
def product_spec(product):
    model_name = product.__class__._meta.model_name
    if isinstance(product, Smartphone):
        if not product.sd:
            PRODUCT_SPEC['smartphone'].pop('Sd capacity')
        else:
            PRODUCT_SPEC['smartphone']['Sd capacity'] = 'sd_volume'
    return mark_safe(TABLE_HEAD + get_product_spec(product=product, model_name=model_name) + TABLE_TAIL)
