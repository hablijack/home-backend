#!/usr/bin/python3
# -*- coding: utf-8 -*-

from tornado.web import RequestHandler


class Energy(RequestHandler):

    def get(self):
        self.render("energy.html")