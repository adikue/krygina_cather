from flask import Flask, request, abort, Response, url_for

from kpoller.db import DbSession, DbEngine


class KpollerApp(object):
    """docstring for KpollerApp"""
    NAME = "kpoller"

    def __init__(self, db_engine, port):
        super(KpollerApp, self).__init__()
        self.db_engine = db_engine
        self.port = int(port)
        self.app = Flask(self.NAME)

        self.app.add_url_rule('/box/', view_func=self.box, methods=['GET'])
        self.app.add_url_rule('/box/<int:box_id>', view_func=self.box,
                              methods=['GET'])

        self.app.add_url_rule('/subscriber/', view_func=self.subscriber,
                              methods=['GET'])
        self.app.add_url_rule('/subscriber/<sub_mail>', view_func=self.subscriber,
                              methods=['GET'])
        self.app.add_url_rule('/subscriber/<sub_mail>/unsubscribe',
                              view_func=self.unsubscribe, methods=['GET'])
        self.app.add_url_rule('/subscriber/<sub_mail>/subscribe',
                              view_func=self.subscribe, methods=['POST'])

        self.app.after_request(self.set_text_header)

    def set_text_header(self, response):
        response.headers["Content-Type"] = "text/plain; charset=utf-8"
        return response

    def get_unsubscribe_url(self, subscriber_mail, box_id):
        with self.app.test_request_context():
            return url_for('unsubscribe', sub_mail=subscriber_mail, box=box_id)

    def run(self):
        self.db = DbSession(self.db_engine)
        self.app.run("0.0.0.0", self.port)

    def box(self, box_id=None):
        if box_id is not None:
            box = self.db.get_box_byid(box_id)
            if not box:
                abort(404)
            return unicode(box)

        return u";\n".join([unicode(b) for b in self.db.get_all_boxes()])

    def subscriber(self, sub_mail=None):
        if sub_mail is not None:
            sub = self.db.get_subscriber_bymail(sub_mail)
            if not sub:
                abort(404)
            return unicode(sub)

        return u";\n".join([unicode(s) for s in self.db.get_active_subs()])

    def unsubscribe(self, sub_mail):
        sub = self.db.get_subscriber_bymail(sub_mail)
        if not sub:
            abort(404)

        box_id = request.args.get("box", 0)
        try:
            box_id = int(box_id)
        except ValueError:
            abort(400, "Query parameter 'box' is not a number")
        if not box_id:
            abort(400, "Query parameter 'box' is empty")

        box = self.db.get_box_byid(box_id)
        if not box:
            abort(400, "Box with id = %d does not exist" % box_id)

        self.db.update_sub_notification(sub, box)
        return u"Ok, %s will no longer receive notifications for box '[%s]: %s'" %\
                (sub_mail, box.month, box.name)

    def subscribe(self, sub_mail):
        sub = self.db.get_subscriber_bymail(sub_mail)
        if not sub:
            abort(404)

        self.db.update_sub_notification(sub, None)
        return u"Ok, %s will receive next notification mail about the box" %\
                sub_mail


def main():
    kapp = KpollerApp(DbEngine("sqlite:////etc/kpoller/kp.db"), port=8008)
    kapp.run()

if __name__ == "__main__":
    main()
