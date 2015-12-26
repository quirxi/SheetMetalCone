#!/usr/bin/env python

from __future__ import division
import sys
sys.path.append('/usr/share/inkscape/extensions')
import math
import simplestyle
import inkex

class SheetMetalConus(inkex.Effect):
    """
    Program to unfold a frustum of a cone or a cone (if parameter diaCut=0) and generate a sheet cutting layout or flat pattern projection 
    that can be rolled or bend up into a (truncated) cone shape.
    """
    # Unit conversion factor from millimetre to pixel (=inkscape standard) and vice versa.
    mm2pixel=3.5433070866
    # Unit conversion factor from inch to pixel (=inkscape standard) and vice versa.
    # Inkscape seems to work with 90 dpi internally ...
    inch2pixel=90
    # default conversion factor between units is millimetre2pixel
    convFactor=mm2pixel

    def __init__(self):
        """
        Constructor.
        Parses the command line options ( Base diameter, cut diameter and height of cone).
        """
        # Call the base class constructor.
        inkex.Effect.__init__(self)

        # Describe parameters
        self.OptionParser.add_option('-b', '--diaBase', action = 'store',
        type = 'float', dest = 'diaBase', default = 300.0000,
        help = 'The diameter of the cones base.')

        self.OptionParser.add_option('-c', '--diaCut', action = 'store',
        type = 'float', dest = 'diaCut', default = 100.0000,
        help = 'The diameter of cones cut (0.0 if cone is not cut.')

        self.OptionParser.add_option('-l', '--heightCone', action = 'store',
        type = 'float', dest = 'heightCone', default = 200.0000,
        help = 'The height of the (cut) cone.')
        
        self.OptionParser.add_option('-u', '--units', action = 'store',
        type = 'string', dest = 'units', default = 'millimetre',
        help = 'The units in which the cone values are given. Can be millimetre or inch.')
        
        self.OptionParser.add_option('-w', '--strokeWidth', action = 'store',
        type = 'float', dest = 'strokeWidth', default = 0.4,
        help = 'The line thickness in given unit. For laser cutting it should be rather small.')

        self.OptionParser.add_option('-f', '--strokeColour', action = 'store',
        type = 'string', dest = 'strokeColour', default = 'blue',
        help = 'The line colour. Can be given in numbers (e.g. \'#000000\') or by name (e.g. \'blue\').')

        self.OptionParser.add_option('-d', '--verbose', action = 'store',
        type = 'inkbool', dest = 'verbose', default = False,
        help = 'Enable verbose output of calculated parameters. Used for debugging or is someone needs the calculated values.')

    def effect(self):
        """
        Effect behaviour.
        Overrides base class' method and draws rolled out sheet metal cone into SVG document.
        """
        if self.options.units == 'inch':
                SheetMetalConus.convFactor=SheetMetalConus.inch2pixel

        # Store all the relevants values in a dictionary for easy access
        dictCone={'diaBase': self.options.diaBase,
                         'diaCut': self.options.diaCut,
                         'heightCone': self.options.heightCone,
                         'units': self.options.units,
                         'conversionFactor': SheetMetalConus.convFactor }

        grp_attribs = {inkex.addNS('label','inkscape') : 'Sheet Metal Conus Group'}
        grp = inkex.etree.SubElement(self.current_layer, 'g', grp_attribs)
        
        # CSS style:
        #style = {'text-align' : 'center', 'text-anchor': 'middle', 'stroke' : 'blue', 'stroke-width': '0.4', 'fill' : 'none'}
        style = {'text-align' : 'center', 'text-anchor': 'middle', 'stroke' : self.options.strokeColour, 
                    'stroke-width': str(self.options.strokeWidth*SheetMetalConus.convFactor), 'fill' : 'none'}
 
        # Get all values needed in order to draw cone layout:
        self.calculateCone( dictCone )
        
        # Draw the cone layout:
        # first connect the points with lines
        self.drawLine(dictCone['ptA'], dictCone['ptB'], style, 'lineAB', grp)
        self.drawLine(dictCone['ptC'], dictCone['ptD'], style, 'lineCD', grp)
        # then connect the points with the arcs:
        # draw an arc with center 0,0 
                # a circle is an ellipse with radiusX=radiusY !
        ptCenter=(0.0, 0.0)
        self.drawEllipse(dictCone['shortRadius'], dictCone['shortRadius'], ptCenter, 0.0, dictCone['angle'], style, 'arcAD', grp)
        self.drawEllipse(dictCone['longRadius'], dictCone['longRadius'], ptCenter, 0.0, dictCone['angle'], style, 'arcBC', grp  )
        
        if self.options.verbose == True:
                self.beVerbose(dictCone)
                
 
    def drawEllipse(self, radiusX, radiusY, (centerX, centerY), startAngle, endAngle, style, name, parent ):
        """
        Draws a ellipse (or arc if radiusX=radiusY) usisng a center point a start angle, an end angle and a given style.
        """
        ell_attribs = {'style' : simplestyle.formatStyle(style),
        inkex.addNS('label','inkscape') : name,
        inkex.addNS('cx','sodipodi')        :str(centerX*SheetMetalConus.convFactor),
        inkex.addNS('cy','sodipodi')        :str(centerY*SheetMetalConus.convFactor),
        inkex.addNS('rx','sodipodi')        :str(radiusX*SheetMetalConus.convFactor),
        inkex.addNS('ry','sodipodi')        :str(radiusY*SheetMetalConus.convFactor),
        inkex.addNS('start','sodipodi')   :str(startAngle),
        inkex.addNS('end','sodipodi')       :str(endAngle),
        inkex.addNS('open','sodipodi')     :'true',    #all ellipse sectors we will draw are open
        inkex.addNS('type','sodipodi')     :'arc' }
        ell = inkex.etree.SubElement(parent, inkex.addNS('path','svg'), ell_attribs )

    def drawLine( self, (x1, y1), (x2, y2), style, name, parent):
        """
        Draws a line from given point 1 to given point 2 with a given style.
        """
        unitFactor=SheetMetalConus.convFactor
        line_attribs = {'style' : simplestyle.formatStyle(style), inkex.addNS('label','inkscape') : name,'d' : 'M '+str(x1*unitFactor)+','+str(y1*unitFactor)+' L '+str(x2*unitFactor)+','+str(y2*unitFactor)}
        line = inkex.etree.SubElement(parent, inkex.addNS('path','svg'), line_attribs )

    def calculateCone( self, dictCone):
        """
        Calculates all relevant values in order to construct a cone.
        These values are:
                * short radius
                * long radius
                * angle of cone layout
                * chord of base diameter
                * chord of cut diameter
                * coordinates of points A, B, C and D
        """        
        dBase=dictCone['diaBase']
        dCut=dictCone['diaCut']
        hCone=dictCone['heightCone']
        # radius from top of cone to cut
        if dCut > 0:
            shortRadius= math.sqrt( ((dCut*dCut)/4)+((dCut*hCone)/(dBase-dCut))*((dCut*hCone)/(dBase-dCut)) )
        else:
            shortRadius=0.0
        dictCone['shortRadius'] = shortRadius
        
        ## radius from top of cone to base of cone
        longRadius=math.sqrt( ((dBase*dBase)/4) + ((dBase*hCone)/(dBase-dCut))*((dBase*hCone)/(dBase-dCut)) )
        dictCone['longRadius'] = longRadius
        ## angle of circle sector
        angle=(math.pi*dBase)/longRadius
        dictCone['angle'] = angle
        # chord is the straight line between the 2 endpoints of an arc. 
        # Not used here, only used if someone needs the calculated values given out in debug output.
        chordBase=longRadius*math.sqrt( 2*(1-math.cos(angle)) )
        dictCone['chordBase'] = chordBase
        chordCut=shortRadius*math.sqrt( 2*(1-math.cos(angle)) )
        dictCone['chordCut'] = chordCut
        # calculate coordinates of points A, B, C and D
        # center M is at (0,0) and points A and B are on the x-axis:
        ptA=(shortRadius,0.0)
        ptB=(longRadius,0.0)
        # we can calculate points C and D with the given radii and the calculated angle
        ptC=(longRadius*math.cos(angle), longRadius*math.sin(angle))
        ptD=(shortRadius*math.cos(angle), shortRadius*math.sin(angle))
        dictCone['ptA'] = ptA
        dictCone['ptB'] = ptB
        dictCone['ptC'] = ptC
        dictCone['ptD'] = ptD

    def beVerbose( self, dictCone ):
        """
        Verbose output of calculated values. Can be used for debugging purposes or if someone needs the calculated values for something else.
        """
        inkex.debug( "Base diameter: " + str(dictCone['diaBase'] ) )
        inkex.debug( "Cut diameter: " + str(dictCone['diaCut'] ) )
        inkex.debug( "Cone height: " + str(dictCone['heightCone'] ) )
        inkex.debug( "Short radius: " + str(dictCone['shortRadius']) )
        inkex.debug( "Long radius: " + str(dictCone['longRadius']) )
        inkex.debug( "Angle of circle sector: " + str(dictCone['angle']) + " radians (= " + str(math.degrees(dictCone['angle'])) + " degrees)")
        inkex.debug( "Chord length of base arc: " + str(dictCone['chordBase']) )
        inkex.debug( "Chord length of cut arc: " + str(dictCone['chordCut']) )
        inkex.debug( "ptA: " + str(dictCone['ptA']) )
        inkex.debug( "ptB: " + str(dictCone['ptB']) )
        inkex.debug( "ptC: " + str(dictCone['ptC']) )
        inkex.debug( "ptD: " + str(dictCone['ptD']) )
        inkex.debug( "DICT: " + str(dictCone) )

# Create effect instance and apply it.
effect = SheetMetalConus()
effect.affect()


