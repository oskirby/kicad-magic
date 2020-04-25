// BGA Ball definitions
ball_top=0.203;  // A1
ball_color=[0.8, 0.8, 0.8];

// BGA Package definitions
pkg_height=1.4; // A
pkg_width=7.0;  // D
pkg_length=7.0; // E
pkg_color=[0.2, 0.2, 0.2];

// Package marking definitions
mark_color=[1, 1, 1];

module bga_ball(x, y, d)
{
    color(ball_color) translate([x, y, d/2])
        sphere(d = d, $fn = 16);
}

module bga_package(length, width, height)
{
    union() {
        // Create the package housing.
        color(pkg_color) translate([-width/2, -length/2, ball_top])
            cube([width, length, height - ball_top]);

        // Add a circular dot to mark ball 1.
        mark_size=(length + width) / 20;
        color(mark_color) translate([mark_size - width/2, length/2 - mark_size, height])
            cylinder(h=0.01, d=mark_size, $fn = 10);
    }
}

