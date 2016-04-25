#!/usr/bin/env python

# Distributed under the terms of the GNU Lesser General Public License v3.0

import sys
#sys.path.append('/usr/share/inkscape/extensions')
import math
import simplestyle
import simpletransform
import inkex

def calc_angle_between_points(p1, p2):
        xDiff = p2[0] - p1[0]
        yDiff = p2[1] - p1[1]
        return math.degrees(math.atan2(yDiff, xDiff))


class SheetMetalConus(inkex.Effect):
    """ Program to unfold a frustum of a cone or a cone 
        (if parameter diaCut=0) and generate a sheet cutting layout
        or flat pattern projection that can be rolled or bend up into a (truncated) cone shape.
    """
    color_marker_dim = '#703cd6'    # purple
    color_marker_chords = '#9d2222' # red
    color_marker_base = '#36ba36'   # green

    def __init__(self):
        """ Parses the command line options ( Base diameter, cut diameter and height of cone).
        """
        inkex.Effect.__init__(self) # Call the base class constructor.
        # Describe parameters
        self.OptionParser.add_option('-b', '--diaBase', action = 'store',
            type = 'float', dest = 'diaBase', default = 300.0,
            help = 'The diameter of the cones base.')

        self.OptionParser.add_option('-c', '--diaCut', action = 'store',
            type = 'float', dest = 'diaCut', default = 100.0,
            help = 'The diameter of cones cut (0.0 if cone is not cut.')

        self.OptionParser.add_option('-l', '--heightCone', action = 'store',
            type = 'float', dest = 'heightCone', default = 200.0,
            help = 'The height of the (cut) cone.')
        
        self.OptionParser.add_option('-u', '--units', action = 'store',
            type = 'string', dest = 'units', default = 'mm',
            help = 'The units in which the cone values are given. mm or in for real objects')
        
        self.OptionParser.add_option('-w', '--strokeWidth', action = 'store',
            type = 'float', dest = 'strokeWidth', default = 0.3,
            help = 'The line thickness in given unit. For laser cutting it should be rather small.')

        self.OptionParser.add_option('-f', '--strokeColour', action = 'store',
            type = 'string', dest = 'strokeColour', default = 896839168, # Blue
            help = 'The line colour.')

        self.OptionParser.add_option('-d', '--verbose', action = 'store',
            type = 'inkbool', dest = 'verbose', default = False,
            help = 'Enable verbose output of calculated parameters. Used for debugging or is someone needs the calculated values.')


    def getUnittouu(self, param):
        " compatibility between inkscape 0.48 and 0.91 "
        try:
            return inkex.unittouu(param)
        except AttributeError:
            return self.unittouu(param)

    def unsignedLong(self, signedLongString):
        " interpret the signed long as unsigned "
        longColor = long(signedLongString)
        if longColor < 0:
            longColor = longColor & 0xFFFFFFFF
        return longColor

    #A*256^0 + B*256^1 + G*256^2 + R*256^3
    def getColorString(self, longColor):
        " convert the long into a #RRGGBB color value "
        longColor = self.unsignedLong(longColor)
        hexColor = hex(longColor)[2:-3]
        hexColor = hexColor.rjust(6, '0')
        return '#' + hexColor.upper()

    def calculateCone(self, dictCone):
        """ Calculates all relevant values in order to construct a cone.
            These values are:
            - short radius
            - long radius
            - angle of cone layout
            - chord of base diameter
            - chord of cut diameter
            - coordinates of points A, B, C and D
        """        
        dBase = dictCone['diaBase']
        dCut =  dictCone['diaCut']
        hCone = dictCone['heightCone']
        base = dBase - dCut
        # radius from top of cone to cut
        if dCut > 0:
            shortRadius = math.sqrt( dCut*dCut/4 + (dCut*hCone)/base * (dCut*hCone)/base )
        else:
            shortRadius=0.0
        dictCone['shortRadius'] = shortRadius
        ## radius from top of cone to base of cone
        longRadius=math.sqrt( dBase*dBase/4 + (dBase*hCone)/base * (dBase*hCone)/base )
        dictCone['longRadius'] = longRadius

        ## angle of circle sector
        angle=(math.pi * dBase) / longRadius
        dictCone['angle'] = angle
        # chord is the straight line between the 2 endpoints of an arc. 
        # Not used directly, but available in verbose output.
        chordBase = longRadius * math.sqrt( 2* (1-math.cos(angle)) )
        dictCone['chordBase'] = chordBase
        chordCut = shortRadius * math.sqrt( 2* (1-math.cos(angle)) )
        dictCone['chordCut'] = chordCut

        # calculate coordinates of points A, B, C and D
        # center M is at (0,0) and points A and B are on the x-axis:
        ptA = (shortRadius, 0.0)
        ptB = (longRadius,  0.0)
        # we can calculate points C and D with the given radii and the calculated angle
        ptC=(longRadius * math.cos(angle),  longRadius *  math.sin(angle))
        ptD=(shortRadius * math.cos(angle), shortRadius * math.sin(angle))
        dictCone['ptA'] = ptA
        dictCone['ptB'] = ptB
        dictCone['ptC'] = ptC
        dictCone['ptD'] = ptD

    def effect(self):
        """ Effect behaviour.
            - Overrides base class' method and draws rolled out sheet metal cone into SVG document.
        """
        # calc scene scale
        convFactor = self.getUnittouu("1" + self.options.units)
        # convert color
        #inkex.debug("%s"%(self.options.strokeColour))
        self.options.strokeColour = self.getColorString(self.options.strokeColour)      
        # Store all the relevants values in a dictionary for easy access
        dictCone={'diaBase':    self.options.diaBase,
                  'diaCut':     self.options.diaCut,
                  'heightCone': self.options.heightCone }
        # Get all values needed in order to draw cone layout:
        self.calculateCone(dictCone)
        
        # Draw the cone layout:
        # Make top level group
        t = 'translate(%s,%s)' % (self.view_center[0], self.view_center[1])
        grp_attribs = {inkex.addNS('label','inkscape'):'Sheet Metal Conus Group', 'transform':t}
        grp = inkex.etree.SubElement(self.current_layer, 'g', grp_attribs)

        linestyle = { 'stroke' : self.options.strokeColour, 'fill' : 'none',
                      'stroke-width': str(self.getUnittouu(str(self.options.strokeWidth) + self.options.units)) }

        # Connect the points with lines
        self.drawLine(dictCone['ptA'], dictCone['ptB'], linestyle, 'lineAB', convFactor, grp)
        self.drawLine(dictCone['ptC'], dictCone['ptD'], linestyle, 'lineCD', convFactor, grp)
        # Connect the points with arcs:
        # draw arc with center 0,0 
        # - a circle is an ellipse with radiusX=radiusY !
        zeroCenter=(0.0, 0.0)
        self.drawEllipse(dictCone['shortRadius'], dictCone['shortRadius'], zeroCenter, 0.0, dictCone['angle'], linestyle, 'arcAD', convFactor, grp)
        self.drawEllipse(dictCone['longRadius'],  dictCone['longRadius'],  zeroCenter, 0.0, dictCone['angle'], linestyle, 'arcBC', convFactor, grp  )
        
        # Draw Dimensions Markup
        if self.options.verbose == True:
            grp_attribs = {inkex.addNS('label','inkscape'):'markup'}
            markup_group = inkex.etree.SubElement(grp, 'g', grp_attribs)
            self.beVerbose(dictCone, convFactor, markup_group)
                
 
    def drawEllipse(self, radiusX, radiusY, (centerX, centerY), startAngle, endAngle, style, label, unitFactor, parent):
        """ Draws an ellipse (or arc if radiusX=radiusY) using
            - center point, start angle, end angle, and a given style.
            unitfactor scales all dimensions.
        """
        attribs = {'style' : simplestyle.formatStyle(style),
        inkex.addNS('label','inkscape') : label,
        inkex.addNS('cx','sodipodi')     :str(centerX * unitFactor),
        inkex.addNS('cy','sodipodi')     :str(centerY * unitFactor),
        inkex.addNS('rx','sodipodi')     :str(radiusX * unitFactor),
        inkex.addNS('ry','sodipodi')     :str(radiusY * unitFactor),
        inkex.addNS('start','sodipodi')  :str(startAngle),
        inkex.addNS('end','sodipodi')    :str(endAngle),
        inkex.addNS('open','sodipodi')   :'true',    #all ellipse sectors we will draw are open
        inkex.addNS('type','sodipodi')   :'arc' }
        ell = inkex.etree.SubElement(parent, inkex.addNS('path','svg'), attribs )

    def drawLine(self, (x1, y1), (x2, y2), style, label, unitFactor, parent):
        """ Draws a line from given point 1 to given point 2 with a given style.
        """
        line_attribs = {'style' : simplestyle.formatStyle(style), inkex.addNS('label','inkscape') : label,
                        'd' : 'M %s,%s L %s,%s' % (x1*unitFactor, y1*unitFactor, x2*unitFactor, y2*unitFactor)}
        line = inkex.etree.SubElement(parent, inkex.addNS('path','svg'), line_attribs )

    def beVerbose(self, dictCone, unitFactor, parent):
        """ Verbose output of calculated values. 
            Can be used for debugging purposes or if calculated values needed.
        """
        # unpack
        base_dia = dictCone['diaBase']
        cut_dia = dictCone['diaCut']
        cone_height = dictCone['heightCone']
        shortradius = dictCone['shortRadius']
        longradius = dictCone['longRadius']
        angle = dictCone['angle']
        chord_base = dictCone['chordBase']
        chord_cut = dictCone['chordCut']
        ptA = dictCone['ptA']
        ptB = dictCone['ptB']
        ptC = dictCone['ptC']
        ptD = dictCone['ptD']

        # styles for markup
        stroke_width = max(0.1, self.getUnittouu(str(self.options.strokeWidth/2) + self.options.units))
        line_style = { 'stroke': self.color_marker_dim, 'stroke-width': str(stroke_width), 'fill':'none' }
        font_height = min(32, max( 10, int(self.getUnittouu(str(cone_height/16) + self.options.units))))
        text_style = { 'font-size': str(font_height),
                       'font-family': 'arial',
                       'text-anchor': 'middle',
                       'text-align': 'center',
                       'fill': self.color_marker_dim }
        # verbose message for debug window
        msg = "Base diameter: " + str(base_dia) + "Cut diameter: " + str(cut_dia) + \
              "\nCone height: " + str(cone_height) + "\nShort radius: " + str(shortradius) + \
              "\nLong radius: " + str(longradius) + "\nAngle of circle sector: " + str(angle) + \
              " radians (= " + str(math.degrees(angle)) + " degrees)" + \
              "\nChord length of base arc: " + str(chord_base) + \
              "\nChord length of cut arc: " + str(chord_cut)
        #inkex.debug( msg)

        # Mark center
        marker_length = max(5, longradius* unitFactor/100)
        line_attribs = {'style' : simplestyle.formatStyle(line_style),
                        inkex.addNS('label','inkscape') : 'center',
                        'd' : 'M -{0},-{0} L {0},{0}'.format(marker_length)}
        line = inkex.etree.SubElement(parent, inkex.addNS('path','svg'), line_attribs)
        line_attribs = {'style' : simplestyle.formatStyle(line_style),
                        inkex.addNS('label','inkscape') : 'center',
                        'd' : 'M -{0},{0} L {0},-{0}'.format(marker_length)}
        line = inkex.etree.SubElement(parent, inkex.addNS('path','svg'), line_attribs)
        # Draw tick marks
        line_attribs = {'style' : simplestyle.formatStyle(line_style), 'd' : 'M 0,0 L 0,-30'}
        line = inkex.etree.SubElement(parent, inkex.addNS('path','svg'), line_attribs)
        if cut_dia != 0:
            line_attribs = {'style' : simplestyle.formatStyle(line_style), 'd' : 'M {0},-3 L {0},-30'.format(shortradius * unitFactor)}
            line = inkex.etree.SubElement(parent, inkex.addNS('path','svg'), line_attribs)
        line_attribs = {'style' : simplestyle.formatStyle(line_style), 'd' : 'M {0},-3 L {0},-30'.format(longradius * unitFactor)}
        line = inkex.etree.SubElement(parent, inkex.addNS('path','svg'), line_attribs)
        # span line
        line_attribs = {'style' : simplestyle.formatStyle(line_style), 'd' : 'M 0,-10 L {0},-10'.format(longradius * unitFactor)}
        line = inkex.etree.SubElement(parent, inkex.addNS('path','svg'), line_attribs)
        # labels for short, long radii
        if cut_dia >= 0.001:
            text_atts = {'style':simplestyle.formatStyle(text_style),
                         'x': str(shortradius*unitFactor/2),
                         'y': str(-15) }
            text = inkex.etree.SubElement(parent, 'text', text_atts)
            text.text = "%4.3f" %(shortradius)
        text_atts = {'style':simplestyle.formatStyle(text_style),
                     'x': str((shortradius + (longradius-shortradius)/2)*unitFactor),
                     'y': str(-15) }
        text = inkex.etree.SubElement(parent, 'text', text_atts)
        text.text = "%4.3f" %(longradius)
        # label for angle
        text_atts = {'style':simplestyle.formatStyle(text_style),
                     'x': '0',
                     'y': str(30) }
        text = inkex.etree.SubElement(parent, 'text', text_atts)
        text.text = "Angle %4.2f" %(math.degrees(angle))
        # chord lines
        dash_style = { 'stroke': self.color_marker_chords, 'stroke-width': str(stroke_width*2),
                       'stroke-miterlimit': '4', 'stroke-dasharray': '4, 2, 1, 2', 'stroke-dashoffset': '0' }
        line_attribs = {'style': simplestyle.formatStyle(dash_style),
                        'd': 'M %f,%f L %f,%f' %(ptA[0]*unitFactor, ptA[1]*unitFactor, ptD[0]*unitFactor, ptD[1]*unitFactor)}
        line = inkex.etree.SubElement(parent, inkex.addNS('path','svg'), line_attribs)
        line_attribs = {'style': simplestyle.formatStyle(dash_style),
                        'd': 'M %f,%f L %f,%f' %(ptB[0]*unitFactor, ptB[1]*unitFactor, ptC[0]*unitFactor, ptC[1]*unitFactor)}
        line = inkex.etree.SubElement(parent, inkex.addNS('path','svg'), line_attribs)
        # chord labels
        centerx = ptB[0]*unitFactor + (ptC[0]-ptB[0])*unitFactor/2
        centery = ptB[1]*unitFactor + (ptC[1]-ptB[1])*unitFactor/2
        line_angle = calc_angle_between_points(ptC, ptB)
        ypos = centery+font_height+2 if line_angle<0 else centery-2
        #inkex.debug("%s"%(line_angle))
        text_style['fill'] = self.color_marker_chords
        text_atts = {'style':simplestyle.formatStyle(text_style),
                     'transform': 'rotate(%f)' % (line_angle) }
        text = inkex.etree.SubElement(parent, 'text', text_atts)
        scale_matrix = [[1, 0.0, centerx], [0.0, 1, ypos]] # needs cos,sin corrections
        simpletransform.applyTransformToNode(scale_matrix, text)
        text.text = "%4.2f" % (chord_base)
        if cut_dia >= 0.001:
            xpos = centerx - font_height*math.sin(math.radians(abs(line_angle)))
            ypos = centery-2 if line_angle<0 else centery+font_height+2
            text = inkex.etree.SubElement(parent, 'text', text_atts)
            scale_matrix = [[1, 0.0, xpos], [0.0, 1, ypos]]
            simpletransform.applyTransformToNode(scale_matrix, text)
            text.text = "%4.2f" % (chord_cut)
        # frustum lines
        frustrum_repos = [[1, 0.0, 1], [0.0, 1, math.sqrt(pow(shortradius*unitFactor,2)-pow(cut_dia*unitFactor/2,2))]]
        text_style['fill'] = self.color_marker_base
        line_style['stroke'] = self.color_marker_base
        line_attribs = {'style': simplestyle.formatStyle(line_style),
                        'd': 'M %f,%f L %f,%f %f,%f %f,%f z' %(-cut_dia/2*unitFactor,0, cut_dia/2*unitFactor,0, base_dia/2*unitFactor,cone_height*unitFactor, -base_dia/2*unitFactor,cone_height*unitFactor)}
        line = inkex.etree.SubElement(parent, inkex.addNS('path','svg'), line_attribs)
        simpletransform.applyTransformToNode(frustrum_repos, line)
        # ticks
        line_attribs = {'style': simplestyle.formatStyle(line_style),
                        'd': 'M %f,%f L %f,%f' %(-(5+cut_dia/2*unitFactor),0, -(5+base_dia/2*unitFactor),0 )}
        line = inkex.etree.SubElement(parent, inkex.addNS('path','svg'), line_attribs)
        simpletransform.applyTransformToNode(frustrum_repos, line)
        line_attribs = {'style': simplestyle.formatStyle(line_style),
                        'd': 'M %f,%f L %f,%f' %(-base_dia/2*unitFactor,0, -base_dia/2*unitFactor,cone_height*unitFactor-5 )}
        line = inkex.etree.SubElement(parent, inkex.addNS('path','svg'), line_attribs)
        simpletransform.applyTransformToNode(frustrum_repos, line)
        # frustum text
        text_atts = {'style':simplestyle.formatStyle(text_style),
                     'x': str(-(18+base_dia/2*unitFactor)),
                     'y': str(cone_height*unitFactor/2) }
        text = inkex.etree.SubElement(parent, 'text', text_atts)
        text.text = "%4.3f" %(cone_height)
        simpletransform.applyTransformToNode(frustrum_repos, text)
        if cut_dia >= 0.001:
            text_atts = {'style':simplestyle.formatStyle(text_style),
                         'x': '0',
                         'y': str(font_height) }
            text = inkex.etree.SubElement(parent, 'text', text_atts)
            text.text = "%4.3f" %(cut_dia)
            simpletransform.applyTransformToNode(frustrum_repos, text)
        text_atts = {'style':simplestyle.formatStyle(text_style),
                     'x': '0',
                     'y': str(cone_height*unitFactor+font_height) }
        text = inkex.etree.SubElement(parent, 'text', text_atts)
        text.text = "%4.3f" %(base_dia)
        simpletransform.applyTransformToNode(frustrum_repos, text)
        
        

# Create effect instance and apply it.
effect = SheetMetalConus()
effect.affect()


