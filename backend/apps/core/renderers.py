from rest_framework.renderers import JSONRenderer


class EnvelopeJSONRenderer(JSONRenderer):
    """
    Wraps successful responses as {"success": true, "message": "", "data": ...}.

    Payloads that already have a `success` key (paginated lists, and errors built
    by api_exception_handler) are passed through unchanged.
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = (renderer_context or {}).get("response")
        already_wrapped = isinstance(data, dict) and "success" in data
        if response is not None and response.status_code < 400 and not already_wrapped:
            data = {"success": True, "message": "", "data": data}
        return super().render(data, accepted_media_type, renderer_context)
