import re

def camel_to_snake(name):
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

def recursive_transform(data, preserve_keys_for=None):
    if preserve_keys_for is None:
        preserve_keys_for = [
            'labels', 'annotations', 'matchLabels', 'nodeSelector', 
            'data', 'binaryData', 'stringData', 'variables', 'commonLabels', 'commonAnnotations'
        ]
    
    if isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            # Convert key to snake_case
            new_key = camel_to_snake(k)
            
            # If the original key is in the preserve list, don't recurse into values' keys 
            # (but we still might need to process values if they are lists of dicts? 
            # No, usually these fields are flat maps or specific structures. 
            # For 'labels', value is str.
            if k in preserve_keys_for:
                new_dict[new_key] = v
            else:
                new_dict[new_key] = recursive_transform(v, preserve_keys_for)
        return new_dict
    elif isinstance(data, list):
        return [recursive_transform(item, preserve_keys_for) for item in data]
    else:
        return data
